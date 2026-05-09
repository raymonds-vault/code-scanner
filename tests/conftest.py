"""Test configuration: SQLite file DB, Redis off, Pinecone init neutralized."""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="shield_test_"))
    db_path = tmp / "shield.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ["REDIS_ENABLED"] = "false"
    os.environ["LLM_BACKEND"] = "stub"
    from app.core.config import get_settings

    get_settings.cache_clear()

    # Neutralize Pinecone init in the FastAPI lifespan so TestClient never
    # contacts a live index. Tests that need Pinecone behavior monkeypatch
    # `get_pinecone_index` directly in app.repositories.pinecone_repo.
    import app.main as main_module

    main_module.init_pinecone_sync = lambda: None  # type: ignore[assignment]
    main_module.close_pinecone = lambda: None  # type: ignore[assignment]


@pytest.fixture(scope="session", autouse=True)
def _init_database() -> None:
    from app.core.database import init_db

    asyncio.run(init_db())


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        yield c
