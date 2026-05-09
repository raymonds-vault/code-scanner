"""Shared helpers for LLM refinement providers."""

import json
import re
from typing import Any

from app.core.config import Settings
from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict


class ProviderError(RuntimeError):
    """Raised when an LLM provider cannot produce a usable draft."""


_JSON_BLOCK = re.compile(r"\{[^{}]*\}", re.DOTALL)


def parse_json_loose(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        match = _JSON_BLOCK.search(text)
        if match:
            parsed = json.loads(match.group())
            return parsed if isinstance(parsed, dict) else {}
    return {}


def build_refinement_prompt(
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> str:
    sig_summary = [f"{s['type']}:{s['confidence']}" for s in signals]
    ctx_docs = "\n".join(context.get("vulnerability_docs", [])[:3])
    return (
        "You are a security assistant. Given static signals and code, output ONLY valid JSON with keys: "
        "type, severity (low|medium|high), confidence (0-1), explanation, fix. "
        "Do not invent issues not supported by signals.\n"
        f"Signals: {sig_summary}\nContext:\n{ctx_docs[:2000]}\nCode:\n{redacted_code[:3000]}\nJSON:"
    )


def draft_from_raw(
    chunk_id: str,
    raw: dict[str, Any],
    signals: list[StaticSignalDict],
) -> LlmDraftDict:
    return {
        "chunk_client_id": chunk_id,
        "type": str(raw.get("type", signals[0]["type"] if signals else "unknown")),
        "severity": str(raw.get("severity", "medium")),
        "confidence": float(raw.get("confidence", 0.5)),
        "explanation": str(raw.get("explanation", "")),
        "fix": str(raw.get("fix", "")),
    }


def provider_quality_score(provider: str, settings: Settings) -> float:
    scores = {
        "openai": 0.9,
        "hf_inference": 0.8,
        "groq": 0.75,
        "transformers": 0.7,
        "stub": 0.0,
    }
    return scores.get(provider, settings.MODEL_QUALITY_GATE)
