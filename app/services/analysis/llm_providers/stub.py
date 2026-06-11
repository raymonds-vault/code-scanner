"""Deterministic LLM provider used by tests and offline runs."""

from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict


async def refine(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    _ = redacted_code, context
    if not signals:
        return {
            "chunk_client_id": chunk_id,
            "type": "informational",
            "severity": "low",
            "confidence": 0.4,
            "explanation": "No strong static signals; stub LLM skipped deep analysis.",
            "fix": "Review manually.",
        }
    s0 = signals[0]
    return {
        "chunk_client_id": chunk_id,
        "type": s0["type"],
        "severity": "high" if s0["confidence"] >= 0.7 else "medium",
        "confidence": min(0.9, float(s0["confidence"]) + 0.05),
        "explanation": f"Refinement aligned with static signal {s0['type']}.",
        "fix": "Validate inputs; use parameterized queries / avoid shell=True.",
    }
