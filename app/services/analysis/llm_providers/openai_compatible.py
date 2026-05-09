"""OpenAI-compatible chat completion providers."""

import httpx

from app.core.config import get_settings
from app.services.analysis.llm_providers.common import (
    ProviderError,
    build_refinement_prompt,
    draft_from_raw,
    parse_json_loose,
)
from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict


def _chat_refine(
    *,
    provider_name: str,
    api_key: str,
    base_url: str,
    model: str,
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    if not api_key.strip():
        raise ProviderError(f"{provider_name} API key is not configured")

    prompt = build_refinement_prompt(redacted_code, signals, context)
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Return only valid JSON for the requested security refinement.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": get_settings().LLM_MAX_NEW_TOKENS,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise ProviderError(f"{provider_name} API error: {exc}") from exc

    try:
        text = str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"{provider_name} response did not include chat content") from exc

    raw = parse_json_loose(text)
    if not raw:
        raise ProviderError(f"{provider_name} returned no parseable JSON")
    return draft_from_raw(chunk_id, raw, signals)


def refine_openai(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    settings = get_settings()
    return _chat_refine(
        provider_name="OpenAI",
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        model=settings.OPENAI_MODEL,
        chunk_id=chunk_id,
        redacted_code=redacted_code,
        signals=signals,
        context=context,
    )


def refine_groq(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    settings = get_settings()
    return _chat_refine(
        provider_name="Groq",
        api_key=settings.GROQ_API_KEY,
        base_url=settings.GROQ_BASE_URL,
        model=settings.GROQ_MODEL,
        chunk_id=chunk_id,
        redacted_code=redacted_code,
        signals=signals,
        context=context,
    )
