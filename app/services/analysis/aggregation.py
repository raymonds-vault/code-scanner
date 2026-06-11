"""Dedupe findings by (file_path, line, type)."""

from app.services.analysis.types import FindingDict

_SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
_SOURCE_RANK = {"static": 1, "llm": 2, "hybrid": 3}


def _score_finding(finding: FindingDict) -> tuple[int, float, int]:
    severity_rank = _SEVERITY_RANK.get(str(finding.get("severity", "")).lower(), 0)
    confidence = float(finding.get("confidence", 0.0))
    source_rank = _SOURCE_RANK.get(str(finding.get("source", "")), 0)
    return (severity_rank, confidence, source_rank)


def dedupe_findings(findings: list[FindingDict]) -> list[FindingDict]:
    by_key: dict[tuple[str, int, str], FindingDict] = {}
    for f in findings:
        key = (f["file_path"], f["line_number"], f["vulnerability_type"].lower())
        previous = by_key.get(key)
        if previous is None or _score_finding(f) > _score_finding(previous):
            by_key[key] = f
    return list(by_key.values())
