"""Health checks."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.dependencies import get_config, get_db
from app.core.pinecone_core import get_pinecone_index
from app.core.redis_client import redis_client
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_config),
) -> HealthResponse:
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    redis_status = "disabled"
    if settings.REDIS_ENABLED:
        redis_status = "healthy"
        try:
            if redis_client:
                await redis_client.ping()
            else:
                redis_status = "unhealthy"
        except Exception:
            redis_status = "unhealthy"

    pinecone_status = "healthy"
    try:
        get_pinecone_index().describe_index_stats()
    except Exception:
        pinecone_status = "unhealthy"

    overall = "healthy" if db_status == "healthy" and pinecone_status == "healthy" else "degraded"
    if redis_status not in ("healthy", "disabled"):
        overall = "degraded"

    return HealthResponse(
        status=overall,
        app_name=settings.APP_NAME,
        database_status=db_status,
        redis_status=redis_status,
        pinecone_status=pinecone_status,
    )
