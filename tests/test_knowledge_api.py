"""Knowledge upload API tests."""

import pytest

from app.core.config import get_settings
from app.services import knowledge_ingest_service


@pytest.fixture(autouse=True)
def _settings_cache_guard():
    yield
    get_settings.cache_clear()


def test_knowledge_document_upload_embeds_to_pinecone(client, monkeypatch) -> None:
    monkeypatch.setenv("PINECONE_NAMESPACE", "tests")
    monkeypatch.setenv("HF_EMBEDDING_MODEL", "test-embedding-model")
    get_settings.cache_clear()

    upserts = []

    def fake_embed(texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def fake_upsert(vectors, texts, payloads, *, namespace=None):
        upserts.append(
            {
                "vectors": vectors,
                "texts": texts,
                "payloads": payloads,
                "namespace": namespace,
            }
        )

    monkeypatch.setattr(knowledge_ingest_service, "embed_texts", fake_embed)
    monkeypatch.setattr(knowledge_ingest_service, "upsert_guideline_chunks", fake_upsert)

    response = client.post(
        "/api/v1/knowledge/documents",
        json={
            "source": "security-guide",
            "category": "injection",
            "doc_version": "2026-05",
            "namespace": "custom",
            "text": "Always parameterize SQL queries.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["chunk_count"] == 1
    assert body["namespace"] == "custom"
    assert body["embedding_model"] == "test-embedding-model"
    assert len(body["content_hashes"]) == 1
    assert upserts[0]["namespace"] == "custom"
    assert upserts[0]["payloads"][0]["category"] == "injection"
