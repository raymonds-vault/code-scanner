"""Redact secrets before embedding / LLM."""

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[=:]\s*['\"]?[^\s'\"]+"), r"\1=****"),
    (
        re.compile(
            r"(?i)\b([a-z0-9_]*(?:secret|token|password|api[_-]?key)[a-z0-9_]*)\s*[=:]\s*['\"]?[^\s'\"]+"
        ),
        r"\1=****",
    ),
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer ****"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "****AWS_ACCESS_KEY****"),
    (
        re.compile(
            r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z]+)? PRIVATE KEY-----",
            re.MULTILINE,
        ),
        "-----BEGIN PRIVATE KEY-----\n****\n-----END PRIVATE KEY-----",
    ),
    (
        re.compile(r"(?i)\b([a-z][a-z0-9+.\-]*://[^:\s/@]+:)([^@\s]+)(@)"),
        r"\1****\3",
    ),
]


def redact_code(text: str) -> str:
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out
