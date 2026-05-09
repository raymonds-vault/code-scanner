"""LangGraph state schema."""

from typing import Any, TypedDict

from app.services.analysis.types import (
    CodeChunkState,
    FindingDict,
    LlmDraftDict,
    StaticSignalDict,
)


class AnalysisState(TypedDict, total=False):
    scan_id: str
    chunks: list[CodeChunkState]
    metadata: dict[str, Any]
    static_signals: list[StaticSignalDict]
    risk_by_chunk_id: dict[str, float]
    chunks_for_llm: list[str]
    llm_outputs: dict[str, LlmDraftDict]
    validated_findings: list[FindingDict]
    errors: list[str]
