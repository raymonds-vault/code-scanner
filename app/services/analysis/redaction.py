"""Redact secrets before embedding / LLM."""

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[=:]\s*['\"]?[^\s'\"]+"), r"\1=****"),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer ****"),
]


def redact_code(text: str) -> str:
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
