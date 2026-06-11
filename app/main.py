"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db, shutdown_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.pinecone_core import close_pinecone, init_pinecone_sync
from app.core.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()

    logger.info("Starting %s...", settings.APP_NAME)
    await init_db()
    await init_redis()
    init_pinecone_sync()

    yield

    logger.info("Shutting down...")
    await close_redis()
    close_pinecone()
    await shutdown_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        description="Security analysis engine with LLM-assisted reasoning.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    from app.controllers.auth_controller import router as auth_router
    from app.controllers.health_controller import router as health_router
    from app.controllers.knowledge_controller import router as knowledge_router
    from app.controllers.scan_controller import router as scan_router

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(knowledge_router, prefix="/api/v1")
    app.include_router(scan_router, prefix="/api/v1")

    return app


app = create_app()
