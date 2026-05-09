"""Scan persistence."""

from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scan_models import Finding, Scan, ScanChunk, StaticSignal


async def create_scan(
    session: AsyncSession,
    *,
    metadata: dict[str, Any],
    client_request_id: str | None,
) -> Scan:
    scan = Scan(
        status="pending",
        progress=0.0,
        metadata_json=metadata,
        client_request_id=client_request_id,
    )
    session.add(scan)
    await session.flush()
    return scan


async def add_chunks(
    session: AsyncSession,
    scan: Scan,
    chunks: Sequence[tuple[str, str, int, int, str, str, str | None, list | None]],
) -> list[ScanChunk]:
    """
    chunks: (client_chunk_id, file_path, start, end, code, language, context_summary, deps)
    """
    rows: list[ScanChunk] = []
    for row in chunks:
        cid, fp, sl, el, code, lang, ctx, deps = row
        ch = ScanChunk(
            scan_id=scan.id,
            client_chunk_id=cid,
            file_path=fp,
            start_line=sl,
            end_line=el,
            code=code,
            language=lang,
            context_summary=ctx,
            dependencies_json=deps,
        )
        session.add(ch)
        rows.append(ch)
    await session.flush()
    return rows


async def get_scan(
    session: AsyncSession, scan_id: str, with_findings: bool = True
) -> Scan | None:
    q = (
        select(Scan)
        .where(Scan.id == scan_id)
        .options(selectinload(Scan.chunks).selectinload(ScanChunk.signals))
    )
    if with_findings:
        q = q.options(selectinload(Scan.findings))
    r = await session.execute(q)
    return r.scalar_one_or_none()


async def update_scan_status(
    session: AsyncSession,
    scan_id: str,
    *,
    status: str | None = None,
    progress: float | None = None,
) -> None:
    scan = await session.get(Scan, scan_id)
    if not scan:
        return
    if status is not None:
        scan.status = status
    if progress is not None:
        scan.progress = progress
    await session.flush()


async def add_signals(
    session: AsyncSession,
    chunk_db_id: str,
    signals: Sequence[tuple[str, float, dict[str, Any]]],
) -> None:
    for stype, conf, loc in signals:
        session.add(
            StaticSignal(
                chunk_id=chunk_db_id,
                signal_type=stype,
                confidence=conf,
                location_json=loc,
            )
        )
    await session.flush()


async def add_findings(
    session: AsyncSession,
    scan_id: str,
    findings: Sequence[
        tuple[str, int, str, str, float, str, str | None, str | None]
    ],
) -> None:
    for fp, ln, vtype, sev, conf, src, expl, fix in findings:
        session.add(
            Finding(
                scan_id=scan_id,
                file_path=fp,
                line_number=ln,
                vulnerability_type=vtype,
                severity=sev,
                confidence=conf,
                source=src,
                explanation=expl,
                fix=fix,
            )
        )
    await session.flush()
