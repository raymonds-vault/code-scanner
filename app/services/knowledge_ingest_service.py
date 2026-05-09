"""Knowledge document ingestion for Pinecone-backed RAG."""

import hashlib
from datetime import UTC, datetime

from app.core.config import get_settings
from app.services.analysis.embedding_service import embed_texts
from app.services.analysis.vector_stores.guidelines import upsert_guideline_chunks


SUPPORTED_KNOWLEDGE_SUFFIXES = {".md", ".txt"}


def chunk_text(text: str, max_chars: int = 1200) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts: list[str] = []
    i = 0
    while i < len(text):
        parts.append(text[i : i + max_chars])
        i += max_chars
    return parts


def ingest_knowledge_text(
    *,
    source: str,
    category: str,
    text: str,
    doc_version: str = "1",
    namespace: str | None = None,
    path: str | None = None,
) -> dict:
    settings = get_settings()
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Knowledge document text is empty")

    ingested_at = datetime.now(UTC).isoformat()
    payloads: list[dict] = []
    content_hashes: list[str] = []
    for idx, chunk in enumerate(chunks):
        content_hash = hashlib.sha256(chunk.encode()).hexdigest()[:16]
        content_hashes.append(content_hash)
        payloads.append(
            {
                "source": source,
                "category": category,
                "doc_version": doc_version,
                "ingested_at": ingested_at,
                "path": path or "",
                "chunk_index": idx,
                "content_hash": content_hash,
            }
        )

    vectors = embed_texts(chunks)
    target_namespace = namespace or settings.PINECONE_NAMESPACE
    upsert_guideline_chunks(vectors, chunks, payloads, namespace=target_namespace)
    return {
        "source": source,
        "category": category,
        "doc_version": doc_version,
        "namespace": target_namespace,
        "embedding_model": settings.HF_EMBEDDING_MODEL or settings.EMBEDDING_MODEL,
        "chunk_count": len(chunks),
        "content_hashes": content_hashes,
    }
