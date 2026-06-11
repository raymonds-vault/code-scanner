"""Merge static + LLM; gate LLM-only low confidence; downgrade on disagreement."""

from app.services.analysis.types import FindingDict, LlmDraftDict, StaticSignalDict

_STATIC_SEVERITY_BY_TYPE = {
    "sql_injection": "high",
    "command_exec": "high",
    "path_traversal": "medium",
}
_VALID_SEVERITIES = {"low", "medium", "high"}


def _normalize_severity(raw: str) -> str:
    sev = str(raw).lower().strip()
    return sev if sev in _VALID_SEVERITIES else "medium"


def _severity_for_static_signal(signal_type: str) -> str:
    return _STATIC_SEVERITY_BY_TYPE.get(signal_type.lower(), "medium")


def validate_and_merge(
    signals: list[StaticSignalDict],
    llm_by_chunk: dict[str, LlmDraftDict],
    *,
    llm_min_confidence: float = 0.6,
) -> list[FindingDict]:
    findings: list[FindingDict] = []
    static_by_client: dict[str, list[StaticSignalDict]] = {}
    for s in signals:
        static_by_client.setdefault(s["chunk_client_id"], []).append(s)

    for s in signals:
        line = int(s["location"].get("start_line", 0))
        findings.append(
            {
                "file_path": str(s["location"].get("file_path", "")),
                "line_number": line,
                "vulnerability_type": s["type"],
                "severity": _severity_for_static_signal(s["type"]),
                "confidence": float(s["confidence"]),
                "source": "static",
                "explanation": None,
                "fix": None,
            }
        )

    for cid, draft in llm_by_chunk.items():
        conf = float(draft.get("confidence", 0.0))
        statics = static_by_client.get(cid, [])
        has_static = len(statics) > 0
        if not has_static and conf < llm_min_confidence:
            continue

        vtype = str(draft.get("type", "unknown"))
        sev = _normalize_severity(str(draft.get("severity", "medium")))
        expl = draft.get("explanation")
        fix = draft.get("fix")

        if has_static:
            st0 = statics[0]
            fp = str(st0["location"].get("file_path", ""))
            line = int(st0["location"].get("start_line", 0))
            static_types = {x["type"].lower() for x in statics}
            if vtype.lower() not in static_types and conf < 0.85:
                sev = "low"
                conf = min(conf, 0.55)
            source: FindingDict["source"] = "hybrid"
        else:
            fp = ""
            line = 0
            source = "llm"

        findings.append(
            {
                "file_path": fp,
                "line_number": line,
                "vulnerability_type": vtype,
                "severity": sev,
                "confidence": conf,
                "source": source,
                "explanation": expl,
                "fix": fix,
            }
        )

    return findings
