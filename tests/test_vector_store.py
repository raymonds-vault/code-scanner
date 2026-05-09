"""Vector store facade tests."""

import pytest

from app.core.config import get_settings
from app.services.analysis import retrieval_service


@pytest.fixture(autouse=True)
def _settings_cache_guard():
    yield
    get_settings.cache_clear()


def test_retrieval_uses_pinecone(monkeypatch) -> None:
    monkeypatch.setenv("PINECONE_NAMESPACE", "tests")
    get_settings.cache_clear()

    class FakeIndex:
        def query(self, **kwargs):
            assert kwargs["namespace"] == "tests"
            assert kwargs["filter"] == {"category": {"$eq": "injection"}}
            return {
                "matches": [
                    {
                        "score": 0.99,
                        "metadata": {
                            "text": "Use parameterized queries.",
                            "source": "guide",
                            "category": "injection",
                        },
                    }
                ]
            }

    fake_index = FakeIndex()
    monkeypatch.setattr(retrieval_service, "embed_one", lambda text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(retrieval_service, "get_pinecone_index", lambda: fake_index)
    monkeypatch.setattr("app.repositories.pinecone_repo.get_pinecone_index", lambda: fake_index)

    context = retrieval_service.retrieve_for_chunk("SELECT * FROM users", signal_category="injection")

    assert context["vulnerability_docs"] == ["Use parameterized queries."]
    assert context["related_patterns"] == ["guide"]


def test_retrieval_returns_empty_when_pinecone_uninitialized(monkeypatch) -> None:
    """When Pinecone isn't initialized (e.g. unit-test lifespan), retrieval is a no-op."""

    def _raise():
        raise RuntimeError("Pinecone not initialized")

    monkeypatch.setattr(retrieval_service, "get_pinecone_index", _raise)
    # embed_one must NOT be called in this path; assert by failing if it is.
    monkeypatch.setattr(
        retrieval_service,
        "embed_one",
        lambda text: pytest.fail("embed_one should not be called when Pinecone is uninitialized"),
    )

    context = retrieval_service.retrieve_for_chunk("SELECT * FROM users", signal_category="injection")

    assert context == {
        "related_patterns": [],
        "similar_code": [],
        "vulnerability_docs": [],
    }
