"""Deterministic static signals (regex / heuristics)."""

import re
from typing import Any

from app.services.analysis.types import CodeChunkState, StaticSignalDict

_SQL = re.compile(
    r"(?i)(cursor\.execute|executemany|\.execute)\s*\(.*(%s|format\s*\(|\+)",
)
_CMD = re.compile(r"(?i)(subprocess\.(run|Popen|call)|os\.system|eval\s*\()")
_PATH = re.compile(r"(?i)(open\s*\(|Path\s*\([^)]*\)\.read)")


def analyze_chunk(chunk: CodeChunkState) -> list[StaticSignalDict]:
    code = chunk["code"]
    base_loc: dict[str, Any] = {
        "file_path": chunk["file_path"],
        "start_line": chunk["start_line"],
        "end_line": chunk["end_line"],
    }
    out: list[StaticSignalDict] = []
    if _SQL.search(code):
        out.append(
            {
                "chunk_client_id": chunk["client_chunk_id"],
                "chunk_db_id": chunk["db_chunk_id"],
                "type": "sql_injection",
                "confidence": 0.75,
                "location": {**base_loc, "pattern": "dynamic_sql"},
            }
        )
    if _CMD.search(code):
        out.append(
            {
                "chunk_client_id": chunk["client_chunk_id"],
                "chunk_db_id": chunk["db_chunk_id"],
                "type": "command_exec",
                "confidence": 0.7,
                "location": {**base_loc, "pattern": "subprocess_or_eval"},
            }
        )
    if _PATH.search(code) and "input" in code.lower():
        out.append(
            {
                "chunk_client_id": chunk["client_chunk_id"],
                "chunk_db_id": chunk["db_chunk_id"],
                "type": "path_traversal",
                "confidence": 0.55,
                "location": {**base_loc, "pattern": "file_and_input"},
            }
        )
    return out
