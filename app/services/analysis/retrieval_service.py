"""RAG context retrieval from Pinecone."""

from app.core.pinecone_core import get_pinecone_index
from app.services.analysis.embedding_service import embed_one
from app.services.analysis.types import ContextBundleDict
from app.services.analysis.vector_stores.guidelines import search_guidelines


def _empty_bundle() -> ContextBundleDict:
    return {
        "related_patterns": [],
        "similar_code": [],
        "vulnerability_docs": [],
    }


def retrieve_for_chunk(
    redacted_code: str,
    *,
    signal_category: str | None = None,
    top_k: int = 5,
) -> ContextBundleDict:
    # Short-circuit before doing any expensive work (embedding model load,
    # network) when Pinecone isn't initialized — e.g. in unit tests.
    try:
        get_pinecone_index()
    except RuntimeError:
        return _empty_bundle()

    qv = embed_one(redacted_code[:8000])
    try:
        hits = search_guidelines(qv, limit=top_k, category_filter=signal_category)
    except RuntimeError:
        return _empty_bundle()
    docs = [h["text"] for h in hits if h.get("text")]
    return {
        "related_patterns": [h.get("source") or "" for h in hits],
        "similar_code": [],
        "vulnerability_docs": docs,
    }
