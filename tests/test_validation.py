"""Validation engine unit tests."""

from app.services.analysis.aggregation import dedupe_findings
from app.services.analysis.validation_engine import validate_and_merge
from app.services.analysis.types import LlmDraftDict, StaticSignalDict


def test_discard_llm_only_low_confidence() -> None:
    llm: dict[str, LlmDraftDict] = {
        "c1": {
            "chunk_client_id": "c1",
            "type": "xss",
            "severity": "high",
            "confidence": 0.3,
            "explanation": "guess",
            "fix": "sanitize",
        }
    }
    out = validate_and_merge([], llm, llm_min_confidence=0.6)
    assert out == []


def test_hybrid_when_static_present() -> None:
    sigs: list[StaticSignalDict] = [
        {
            "chunk_client_id": "c1",
            "chunk_db_id": "d1",
            "type": "sql_injection",
            "confidence": 0.8,
            "location": {"file_path": "a.py", "start_line": 3},
        }
    ]
    llm: dict[str, LlmDraftDict] = {
        "c1": {
            "chunk_client_id": "c1",
            "type": "sql_injection",
            "severity": "high",
            "confidence": 0.75,
            "explanation": "refined",
            "fix": "use params",
        }
    }
    out = validate_and_merge(sigs, llm)
    types = {x["vulnerability_type"] for x in out}
    assert "sql_injection" in types
    sources = {x["source"] for x in out}
    assert "hybrid" in sources or "static" in sources


def test_static_severity_mapping() -> None:
    sigs: list[StaticSignalDict] = [
        {
            "chunk_client_id": "c1",
            "chunk_db_id": "d1",
            "type": "sql_injection",
            "confidence": 0.8,
            "location": {"file_path": "a.py", "start_line": 3},
        },
        {
            "chunk_client_id": "c2",
            "chunk_db_id": "d2",
            "type": "path_traversal",
            "confidence": 0.55,
            "location": {"file_path": "b.py", "start_line": 7},
        },
    ]

    out = validate_and_merge(sigs, {})
    by_type = {finding["vulnerability_type"]: finding for finding in out}

    assert by_type["sql_injection"]["severity"] == "high"
    assert by_type["path_traversal"]["severity"] == "medium"


def test_dedupe_prefers_stronger_finding() -> None:
    rows = [
        {
            "file_path": "a.py",
            "line_number": 1,
            "vulnerability_type": "x",
            "severity": "low",
            "confidence": 0.5,
            "source": "static",
            "explanation": None,
            "fix": None,
        },
        {
            "file_path": "a.py",
            "line_number": 1,
            "vulnerability_type": "x",
            "severity": "high",
            "confidence": 0.6,
            "source": "llm",
            "explanation": None,
            "fix": None,
        },
    ]
    out = dedupe_findings(rows)
    assert len(out) == 1
    assert out[0]["severity"] == "high"
