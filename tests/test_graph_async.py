"""Async behavior tests for graph execution."""

import asyncio
import time

import pytest

from app.core.config import get_settings
from app.services.analysis import graph


@pytest.fixture(autouse=True)
def _settings_cache_guard():
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_node_rag_llm_runs_selected_chunks_concurrently(monkeypatch) -> None:
    monkeypatch.setenv("MAX_CONCURRENCY", "4")
    get_settings.cache_clear()

    in_flight = 0
    peak_in_flight = 0
    lock = asyncio.Lock()

    async def fake_retrieve_for_chunk(*args, **kwargs):
        await asyncio.sleep(0.2)
        return {"related_patterns": [], "similar_code": [], "vulnerability_docs": []}

    async def fake_refine_chunk(chunk_id, redacted_code, signals, context):
        nonlocal in_flight, peak_in_flight
        async with lock:
            in_flight += 1
            peak_in_flight = max(peak_in_flight, in_flight)
        try:
            await asyncio.sleep(0.2)
            return {
                "chunk_client_id": chunk_id,
                "type": "sql_injection",
                "severity": "high",
                "confidence": 0.9,
                "explanation": "mock",
                "fix": "mock",
            }
        finally:
            async with lock:
                in_flight -= 1

    monkeypatch.setattr(graph, "retrieve_for_chunk", fake_retrieve_for_chunk)
    monkeypatch.setattr(graph, "refine_chunk", fake_refine_chunk)

    chunks = [
        {
            "client_chunk_id": f"c{i}",
            "db_chunk_id": f"d{i}",
            "file_path": "a.py",
            "start_line": 1,
            "end_line": 2,
            "code": "print(1)",
            "language": "python",
            "context_summary": None,
            "dependencies": None,
        }
        for i in range(4)
    ]
    state = {
        "scan_id": "scan-1",
        "chunks": chunks,
        "chunks_for_llm": [c["client_chunk_id"] for c in chunks],
        "static_signals": [],
    }
    config = {"configurable": {"publish": None}}

    started = time.perf_counter()
    out = await graph.node_rag_llm(state, config)
    elapsed = time.perf_counter() - started

    assert len(out["llm_outputs"]) == 4
    assert peak_in_flight >= 2
    assert elapsed < 0.8
