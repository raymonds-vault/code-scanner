"""Scan REST + WebSocket."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_optional_user, require_user
from app.core.database import AsyncSessionLocal
from app.core.dependencies import get_db
from app.core.exceptions import NotFoundException
from app.repositories import scan_repo
from app.schemas.scan import (
    FindingOut,
    ScanCreatedResponse,
    ScanDetailResponse,
    ScanListResponse,
    ScanRequest,
)
from app.services.scan_events import broker
from app.services.scan_service import persist_scan_request, schedule_scan_analysis

router = APIRouter(tags=["Scan"], prefix="/scan")


@router.get("s", response_model=ScanListResponse)
async def list_scans(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_user),
) -> ScanListResponse:
    scans, total = await scan_repo.list_scans_by_user(
        db, current_user["sub"], limit=limit, offset=offset
    )
    return ScanListResponse(scans=scans, total=total)


@router.post("", response_model=ScanCreatedResponse)
async def create_scan(
    body: ScanRequest,
    current_user: dict | None = Depends(get_optional_user),
) -> ScanCreatedResponse:
    user_id = current_user["sub"] if current_user else None
    meta = body.metadata.model_dump()
    tuples = [
        (
            c.id,
            c.file_path,
            c.start_line,
            c.end_line,
            c.code,
            c.language,
            c.context_summary,
            c.dependencies,
        )
        for c in body.chunks
    ]
    async with AsyncSessionLocal() as session:
        scan_id = await persist_scan_request(
            session,
            client_request_id=body.client_request_id,
            metadata=meta,
            chunks=tuples,
            user_id=user_id,
        )
        await session.commit()
    schedule_scan_analysis(scan_id)
    return ScanCreatedResponse(id=scan_id, status="pending")


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScanDetailResponse:
    scan = await scan_repo.get_scan(db, scan_id, with_findings=True)
    if not scan:
        raise NotFoundException("Scan", scan_id)
    findings = [
        FindingOut(
            id=f.id,
            file_path=f.file_path,
            line_number=f.line_number,
            vulnerability_type=f.vulnerability_type,
            severity=f.severity,
            confidence=f.confidence,
            source=f.source,
            explanation=f.explanation,
            fix=f.fix,
        )
        for f in (scan.findings or [])
    ]
    return ScanDetailResponse(
        id=scan.id,
        status=scan.status,
        progress=scan.progress,
        metadata=scan.metadata_json or {},
        findings=findings,
    )


@router.websocket("/{scan_id}/stream")
async def scan_stream(ws: WebSocket, scan_id: str) -> None:
    await broker.connect(scan_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await broker.disconnect(scan_id, ws)
