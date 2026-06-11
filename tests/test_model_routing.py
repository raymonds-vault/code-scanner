"""LLM provider routing tests."""

import pytest

from app.core.config import get_settings
from app.services.analysis.llm_providers import router
from app.services.analysis.llm_providers.common import ProviderError
from app.services.analysis.llm_providers.openai_compatible import refine_openai


@pytest.fixture(autouse=True)
def _settings_cache_guard():
    yield
    get_settings.cache_clear()


def _clear_settings() -> None:
    get_settings.cache_clear()


def test_speed_policy_prefers_groq(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "routed")
    monkeypatch.setenv("MODEL_ROUTING_POLICY", "speed")
    monkeypatch.setenv("MODEL_SPEED_PREFERENCE", "fast")
    monkeypatch.setenv("MODEL_QUALITY_GATE", "0.7")
    _clear_settings()

    assert router.candidates_for_settings()[0] == "groq"


@pytest.mark.asyncio
async def test_provider_failure_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "routed")
    monkeypatch.setenv("MODEL_ROUTING_POLICY", "speed")
    monkeypatch.setenv("MODEL_SPEED_PREFERENCE", "fast")
    monkeypatch.setenv("MODEL_QUALITY_GATE", "0.7")
    _clear_settings()

    async def fail_provider(*args, **kwargs):
        raise ProviderError("provider unavailable")

    async def ok_provider(chunk_id, redacted_code, signals, context):
        return {
            "chunk_client_id": chunk_id,
            "type": "sql_injection",
            "severity": "high",
            "confidence": 0.8,
            "explanation": "mocked",
            "fix": "mocked",
        }

    monkeypatch.setitem(router.PROVIDERS, "groq", fail_provider)
    monkeypatch.setitem(router.PROVIDERS, "openai", ok_provider)

    draft = await router.refine_with_router("c1", "code", [], {})

    assert draft["provider"] == "openai"
    assert draft["type"] == "sql_injection"


@pytest.mark.asyncio
async def test_openai_provider_parses_chat_completion(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    _clear_settings()

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"type":"command_injection","severity":"high",'
                                '"confidence":0.91,"explanation":"risky","fix":"sanitize"}'
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, url, headers, json):
            assert url.endswith("/chat/completions")
            assert headers["Authorization"] == "Bearer test-key"
            assert json["model"] == "test-model"
            return FakeResponse()

    monkeypatch.setattr(
        "app.services.analysis.llm_providers.openai_compatible.httpx.AsyncClient",
        FakeClient,
    )

    draft = await refine_openai("c1", "code", [], {})

    assert draft["type"] == "command_injection"
    assert draft["confidence"] == 0.91


@pytest.mark.asyncio
async def test_router_fallback_message_is_sanitized(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BACKEND", "routed")
    monkeypatch.setenv("MODEL_ROUTING_POLICY", "speed")
    monkeypatch.setenv("MODEL_SPEED_PREFERENCE", "fast")
    monkeypatch.setenv("MODEL_QUALITY_GATE", "0.0")
    _clear_settings()

    async def fail_provider(*args, **kwargs):
        raise ProviderError("HTTP 401 token=secret-value")

    monkeypatch.setitem(router.PROVIDERS, "groq", fail_provider)
    monkeypatch.setitem(router.PROVIDERS, "openai", fail_provider)
    monkeypatch.setitem(router.PROVIDERS, "hf_inference", fail_provider)
    monkeypatch.setitem(router.PROVIDERS, "transformers", fail_provider)

    draft = await router.refine_with_router("c1", "code", [], {})

    assert draft["provider"] == "stub"
    assert draft["provider_fallback"] is True
    assert "secret-value" not in draft["explanation"]
    assert "Provider fallback was applied" in draft["explanation"]
