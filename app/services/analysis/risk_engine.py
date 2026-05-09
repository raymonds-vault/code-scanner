"""Risk score per chunk to gate LLM usage."""

from app.services.analysis.types import CodeChunkState, StaticSignalDict


def score_chunk(
    chunk: CodeChunkState,
    signals: list[StaticSignalDict],
    *,
    pattern_weight: float = 0.45,
    sensitive_weight: float = 0.25,
    input_flow_weight: float = 0.2,
) -> float:
    """Higher score => more likely to send to LLM."""
    base = 0.0
    for s in signals:
        if s["chunk_client_id"] != chunk["client_chunk_id"]:
            continue
        base += pattern_weight * float(s["confidence"])
    text = chunk["code"].lower()
    if any(x in text for x in ("password", "secret", "token", "api_key")):
        base += sensitive_weight
    if any(x in text for x in ("request.", "input(", "argv", "getparameter")):
        base += input_flow_weight
    return min(1.0, base)
