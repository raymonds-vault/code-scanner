"""Shared typed payloads for the analysis pipeline."""

from typing import Any, Literal, TypedDict


class CodeChunkState(TypedDict):
    client_chunk_id: str
    db_chunk_id: str
    file_path: str
    start_line: int
    end_line: int
    code: str
    language: str
    context_summary: str | None
    dependencies: list[str] | None


class StaticSignalDict(TypedDict):
    chunk_client_id: str
    chunk_db_id: str
    type: str
    confidence: float
    location: dict[str, Any]


class ContextBundleDict(TypedDict, total=False):
    related_patterns: list[str]
    similar_code: list[str]
    vulnerability_docs: list[str]


class LlmDraftDict(TypedDict, total=False):
    chunk_client_id: str
    type: str
    severity: str
    confidence: float
    explanation: str
    fix: str
    provider: str
    provider_fallback: bool


class FindingDict(TypedDict):
    file_path: str
    line_number: int
    vulnerability_type: str
    severity: str
    confidence: float
    source: Literal["static", "llm", "hybrid"]
    explanation: str | None
    fix: str | None
