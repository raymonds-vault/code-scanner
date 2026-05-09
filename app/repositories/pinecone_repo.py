"""Pinecone operations for security guidelines RAG."""

import hashlib
import uuid
from typing import Any

from app.core.config import get_settings
from app.core.pinecone_core import get_pinecone_index


def _point_id(source: str, chunk_index: int, text_hash: str) -> str:
    raw = f"{source}:{chunk_index}:{text_hash}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


def _metadata_from_match(match: Any) -> dict[str, Any]:
    if isinstance(match, dict):
        return dict(match.get("metadata") or {})
    return dict(getattr(match, "metadata", None) or {})


def _score_from_match(match: Any) -> float:
    if isinstance(match, dict):
        return float(match.get("score", 0.0))
    return float(getattr(match, "score", 0.0) or 0.0)


def upsert_guideline_chunks(
    vectors: list[list[float]],
    texts: list[str],
    payloads: list[dict[str, Any]],
    *,
    namespace: str | None = None,
) -> None:
    settings = get_settings()
    index = get_pinecone_index()
    target_namespace = namespace or settings.PINECONE_NAMESPACE
    pinecone_vectors: list[dict[str, Any]] = []
    for i, (vec, text, payload) in enumerate(zip(vectors, texts, payloads, strict=True)):
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        pid = _point_id(str(payload.get("source", "")), i, text_hash)
        pinecone_vectors.append(
            {
                "id": pid,
                "values": vec,
                "metadata": {**payload, "text": text, "content_hash": payload.get("content_hash", text_hash)},
            }
        )
    index.upsert(vectors=pinecone_vectors, namespace=target_namespace)


def search_guidelines(
    query_vector: list[float],
    *,
    limit: int = 5,
    category_filter: str | None = None,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    index = get_pinecone_index()
    target_namespace = namespace or settings.PINECONE_NAMESPACE
    metadata_filter = {"category": {"$eq": category_filter}} if category_filter else None
    response = index.query(
        vector=query_vector,
        top_k=limit,
        namespace=target_namespace,
        filter=metadata_filter,
        include_metadata=True,
    )
    matches = response.get("matches", []) if isinstance(response, dict) else getattr(response, "matches", [])
    out: list[dict[str, Any]] = []
    for match in matches:
        metadata = _metadata_from_match(match)
        out.append(
            {
                "score": _score_from_match(match),
                "text": metadata.get("text", ""),
                "source": metadata.get("source"),
                "category": metadata.get("category"),
            }
        )
    return out
