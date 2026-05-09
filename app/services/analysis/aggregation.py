"""Dedupe findings by (file_path, line, type)."""

from app.services.analysis.types import FindingDict


def dedupe_findings(findings: list[FindingDict]) -> list[FindingDict]:
    seen: set[tuple[str, int, str]] = set()
    out: list[FindingDict] = []
    for f in findings:
        key = (f["file_path"], f["line_number"], f["vulnerability_type"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out
