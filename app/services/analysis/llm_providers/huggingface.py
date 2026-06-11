"""Hugging Face hosted and local refinement providers."""

import httpx

from app.core.config import get_settings
from app.services.analysis.llm_providers.common import (
    ProviderError,
    build_refinement_prompt,
    draft_from_raw,
    parse_json_loose,
)
from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict


async def refine_inference(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    """Hugging Face Inference API provider."""
    settings = get_settings()
    if not settings.HF_TOKEN.strip():
        raise ProviderError("HF_TOKEN is not configured")

    prompt = build_refinement_prompt(redacted_code, signals, context)
    url = f"{settings.HF_INFERENCE_BASE_URL.rstrip('/')}/models/{settings.LLM_MODEL}"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
    payload: dict = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": settings.LLM_MAX_NEW_TOKENS,
            "return_full_text": False,
        },
    }
    timeout = httpx.Timeout(connect=10.0, read=45.0, write=30.0, pool=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        raise ProviderError(f"HF Inference API error: {exc}") from exc

    text = ""
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            text = str(first.get("generated_text", ""))
    elif isinstance(data, dict):
        text = str(data.get("generated_text", data.get("text", "")))

    raw = parse_json_loose(text.split("JSON:")[-1] if "JSON:" in text else text)
    if not raw:
        raw = parse_json_loose(text)
    if not raw:
        raise ProviderError("HF Inference API returned no parseable JSON")
    return draft_from_raw(chunk_id, raw, signals)


def refine_transformers(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    """Local transformers provider."""
    settings = get_settings()
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ProviderError("transformers dependencies are not installed") from exc

    prompt = build_refinement_prompt(redacted_code, signals, context)
    tok = AutoTokenizer.from_pretrained(settings.LLM_MODEL, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        settings.LLM_MODEL,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
    )
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=2048)
    if torch.cuda.is_available():
        inputs = {k: v.cuda() for k, v in inputs.items()}
    out = model.generate(
        **inputs,
        max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
        do_sample=False,
    )
    text = tok.decode(out[0], skip_special_tokens=True)
    raw = parse_json_loose(text.split("JSON:")[-1])
    if not raw:
        raise ProviderError("transformers provider returned no parseable JSON")
    return draft_from_raw(chunk_id, raw, signals)
