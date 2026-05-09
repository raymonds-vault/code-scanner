"""Scan API schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    id: str
    file_path: str
    start_line: int
    end_line: int
    code: str
    language: str = "unknown"
    context_summary: str | None = None
    dependencies: list[str] | None = None


class ScanMetadata(BaseModel):
    repo_root: str | None = None
    commit: str | None = None
    mode: Literal["local_only", "hybrid", "cloud_enhanced"] | None = "local_only"
    extra: dict[str, Any] = Field(default_factory=dict)


class ScanRequest(BaseModel):
    client_request_id: str | None = None
    chunks: list[CodeChunk]
    metadata: ScanMetadata = Field(default_factory=ScanMetadata)


class ScanCreatedResponse(BaseModel):
    id: str
    status: str


class FindingOut(BaseModel):
    id: str
    file_path: str
    line_number: int
    vulnerability_type: str
    severity: str
    confidence: float
    source: str
    explanation: str | None = None
    fix: str | None = None


class ScanDetailResponse(BaseModel):
    id: str
    status: str
    progress: float
    metadata: dict[str, Any]
    findings: list[FindingOut]


class StreamEvent(BaseModel):
    """WebSocket / SSE-style event envelope."""

    event: Literal[
        "progress",
        "chunk_started",
        "static_signal",
        "llm_skipped",
        "finding",
        "error",
        "completed",
    ]
    scan_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
