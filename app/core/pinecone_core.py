"""Pinecone client lifecycle."""

from typing import Any

from app.core.config import get_settings

_pinecone_index: Any | None = None


def get_pinecone_index() -> Any:
    if _pinecone_index is None:
        raise RuntimeError("Pinecone not initialized")
    return _pinecone_index


def init_pinecone_sync() -> Any:
    """Create the configured Pinecone index handle."""
    global _pinecone_index
    settings = get_settings()
    if not settings.PINECONE_API_KEY.strip():
        raise RuntimeError("PINECONE_API_KEY is required")
    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise RuntimeError("pinecone package is required") from exc

    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    if settings.PINECONE_HOST.strip():
        _pinecone_index = pc.Index(host=settings.PINECONE_HOST)
    else:
        _pinecone_index = pc.Index(settings.PINECONE_INDEX_NAME)
    return _pinecone_index


def close_pinecone() -> None:
    global _pinecone_index
    _pinecone_index = None
