"""Provider routing for LLM refinement."""

import asyncio
from collections.abc import Awaitable, Callable

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.services.analysis.llm_providers import stub
from app.services.analysis.llm_providers.common import ProviderError, provider_quality_score
from app.services.analysis.llm_providers.huggingface import (
    refine_inference,
    refine_transformers,
)
from app.services.analysis.llm_providers.openai_compatible import refine_groq, refine_openai
from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict

logger = get_logger(__name__)

ProviderFn = Callable[
    [str, str, list[StaticSignalDict], ContextBundleDict],
    Awaitable[LlmDraftDict],
]

def _refine_transformers_async(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> Awaitable[LlmDraftDict]:
    return asyncio.to_thread(refine_transformers, chunk_id, redacted_code, signals, context)


PROVIDERS: dict[str, ProviderFn] = {
    "stub": stub.refine,
    "hf_inference": refine_inference,
    "transformers": _refine_transformers_async,
    "groq": refine_groq,
    "openai": refine_openai,
}


def _with_fallback_note(draft: LlmDraftDict) -> LlmDraftDict:
    explanation = str(draft.get("explanation", "")).strip()
    suffix = "Provider fallback was applied due to upstream model availability."
    draft["explanation"] = f"{explanation} {suffix}".strip()
    draft["provider_fallback"] = True
    return draft


def _fallback_order(settings: Settings) -> list[str]:
    order = [p.strip().lower() for p in settings.MODEL_FALLBACK_ORDER.split(",") if p.strip()]
    return [p for p in order if p in PROVIDERS]


def _routed_candidates(settings: Settings) -> list[str]:
    policy = settings.MODEL_ROUTING_POLICY.lower()
    speed = settings.MODEL_SPEED_PREFERENCE.lower()
    if policy == "quality" or speed == "quality":
        candidates = ["openai", "hf_inference", "groq", "transformers", "stub"]
    elif policy == "speed" or speed == "fast":
        candidates = ["groq", "openai", "hf_inference", "transformers", "stub"]
    else:
        candidates = _fallback_order(settings)

    gate = float(settings.MODEL_QUALITY_GATE)
    gated = [
        provider
        for provider in candidates
        if provider == "stub" or provider_quality_score(provider, settings) >= gate
    ]
    return gated or ["stub"]


def candidates_for_settings(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    backend = settings.LLM_BACKEND.lower()
    if backend in ("routed", "auto"):
        return _routed_candidates(settings)
    if backend in PROVIDERS:
        return [backend, "stub"] if backend != "stub" else ["stub"]
    logger.warning("Unknown LLM_BACKEND=%s; using routed policy", settings.LLM_BACKEND)
    return _routed_candidates(settings)


async def refine_with_router(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    had_provider_fallback = False
    for provider in candidates_for_settings():
        try:
            draft = await PROVIDERS[provider](chunk_id, redacted_code, signals, context)
            draft["provider"] = provider
            if had_provider_fallback:
                _with_fallback_note(draft)
            return draft
        except ProviderError as exc:
            had_provider_fallback = True
            logger.warning("LLM provider %s failed for chunk %s: %s", provider, chunk_id, exc)
        except Exception:
            had_provider_fallback = True
            logger.exception("Unexpected LLM provider failure for chunk %s", chunk_id)
    draft = await stub.refine(chunk_id, redacted_code, signals, context)
    draft["provider"] = "stub"
    if had_provider_fallback:
        _with_fallback_note(draft)
    return draft
