"""Scan lifecycle and LangGraph execution."""

import asyncio
import traceback

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.repositories import scan_repo
from app.schemas.scan import StreamEvent
from app.services.analysis.graph import build_graph
from app.services.analysis.types import CodeChunkState
from app.services.scan_events import broker

logger = get_logger(__name__)
_graph = None


def get_analysis_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _chunks_to_state(rows: list) -> list[CodeChunkState]:
    out: list[CodeChunkState] = []
    for c in rows:
        deps = c.dependencies_json if isinstance(c.dependencies_json, list) else None
        out.append(
            CodeChunkState(
                client_chunk_id=c.client_chunk_id,
                db_chunk_id=c.id,
                file_path=c.file_path,
                start_line=c.start_line,
                end_line=c.end_line,
                code=c.code,
                language=c.language,
                context_summary=c.context_summary,
                dependencies=deps,
            )
        )
    return out


async def run_analysis_job(scan_id: str) -> None:
    async with AsyncSessionLocal() as session:
        try:
            scan = await scan_repo.get_scan(session, scan_id, with_findings=False)
            if not scan:
                logger.error("Scan %s not found", scan_id)
                return
            await scan_repo.update_scan_status(session, scan_id, status="running", progress=0.02)
            await session.commit()

            chunks_state = _chunks_to_state(list(scan.chunks))

            async def publish(ev: StreamEvent) -> None:
                await broker.publish(scan_id, ev)

            initial = {
                "scan_id": scan_id,
                "chunks": chunks_state,
                "metadata": scan.metadata_json or {},
            }
            graph = get_analysis_graph()
            await graph.ainvoke(
                initial,
                config={"configurable": {"db_session": session, "publish": publish}},
            )
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Scan %s failed", scan_id)
            tb = traceback.format_exc()
            async with AsyncSessionLocal() as s2:
                await scan_repo.update_scan_status(s2, scan_id, status="failed", progress=0.0)
                await s2.commit()
            await broker.publish(
                scan_id,
                StreamEvent(
                    event="error",
                    scan_id=scan_id,
                    payload={"detail": tb[-2000:]},
                ),
            )


def schedule_scan_analysis(scan_id: str) -> None:
    asyncio.create_task(run_analysis_job(scan_id))


async def persist_scan_request(
    session: AsyncSession,
    *,
    client_request_id: str | None,
    metadata: dict,
    chunks: list[tuple],
) -> str:
    scan = await scan_repo.create_scan(
        session, metadata=metadata, client_request_id=client_request_id
    )
    await scan_repo.add_chunks(session, scan, chunks)
    await session.flush()
    return scan.id
