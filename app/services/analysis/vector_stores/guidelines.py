"""Vector-store facade for security guideline RAG (Pinecone-backed)."""

from typing import Any

from app.repositories import pinecone_repo


def upsert_guideline_chunks(
    vectors: list[list[float]],
    texts: list[str],
    payloads: list[dict[str, Any]],
    *,
    namespace: str | None = None,
) -> None:
    pinecone_repo.upsert_guideline_chunks(vectors, texts, payloads, namespace=namespace)


def search_guidelines(
    query_vector: list[float],
    *,
    limit: int = 5,
    category_filter: str | None = None,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    return pinecone_repo.search_guidelines(
        query_vector,
        limit=limit,
        category_filter=category_filter,
        namespace=namespace,
    )
