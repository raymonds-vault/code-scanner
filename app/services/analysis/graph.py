"""LangGraph: single LLM refinement node; static is primary detection."""

import asyncio
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.repositories import scan_repo
from app.schemas.scan import StreamEvent
from app.services.analysis.aggregation import dedupe_findings
from app.services.analysis.llm_refinement import refine_chunk
from app.services.analysis.redaction import redact_code
from app.services.analysis.retrieval_service import retrieve_for_chunk
from app.services.analysis.risk_engine import score_chunk
from app.services.analysis.state import AnalysisState
from app.services.analysis.static_analyzer import analyze_chunk
from app.services.analysis.validation_engine import validate_and_merge


async def _emit(config: RunnableConfig, event: StreamEvent) -> None:
    pub = config.get("configurable", {}).get("publish")
    if pub:
        await pub(event)


def _session(config: RunnableConfig) -> Any:
    return config["configurable"]["db_session"]


async def node_normalize(state: AnalysisState, config: RunnableConfig) -> dict[str, Any]:
    await _emit(
        config,
        StreamEvent(
            event="progress",
            scan_id=state["scan_id"],
            payload={"phase": "normalize", "progress": 0.05},
        ),
    )
    return {}


async def node_static(state: AnalysisState, config: RunnableConfig) -> dict[str, Any]:
    session = _session(config)
    signals: list = []
    for ch in state["chunks"]:
        found = analyze_chunk(ch)
        signals.extend(found)
        await _emit(
            config,
            StreamEvent(
                event="chunk_started",
                scan_id=state["scan_id"],
                payload={"chunk_id": ch["client_chunk_id"]},
            ),
        )
        if found:
            await scan_repo.add_signals(
                session,
                ch["db_chunk_id"],
                [(s["type"], s["confidence"], s["location"]) for s in found],
            )
        for s in found:
            await _emit(
                config,
                StreamEvent(
                    event="static_signal",
                    scan_id=state["scan_id"],
                    payload={"chunk_id": ch["client_chunk_id"], "signal": s["type"]},
                ),
            )
    return {"static_signals": signals}


async def node_risk_select(state: AnalysisState, config: RunnableConfig) -> dict[str, Any]:
    settings = get_settings()
    risks: dict[str, float] = {}
    for ch in state["chunks"]:
        sigs = [s for s in state.get("static_signals", []) if s["chunk_client_id"] == ch["client_chunk_id"]]
        risks[ch["client_chunk_id"]] = score_chunk(ch, sigs)
    ranked = sorted(risks.items(), key=lambda x: x[1], reverse=True)
    selected: list[str] = []
    for cid, score in ranked:
        if score < settings.RISK_THRESHOLD:
            await _emit(
                config,
                StreamEvent(
                    event="llm_skipped",
                    scan_id=state["scan_id"],
                    payload={"chunk_id": cid, "risk": score},
                ),
            )
            continue
        if len(selected) >= settings.MAX_LLM_CHUNKS:
            await _emit(
                config,
                StreamEvent(
                    event="llm_skipped",
                    scan_id=state["scan_id"],
                    payload={"chunk_id": cid, "risk": score, "reason": "max_llm_chunks"},
                ),
            )
            continue
        selected.append(cid)
    await _emit(
        config,
        StreamEvent(
            event="progress",
            scan_id=state["scan_id"],
            payload={"phase": "risk_select", "progress": 0.35},
        ),
    )
    return {"risk_by_chunk_id": risks, "chunks_for_llm": selected}


async def node_rag_llm(state: AnalysisState, config: RunnableConfig) -> dict[str, Any]:
    settings = get_settings()
    sem = asyncio.Semaphore(settings.MAX_CONCURRENCY)
    chunk_by_id = {c["client_chunk_id"]: c for c in state["chunks"]}
    llm_out: dict[str, Any] = {}

    async def one(cid: str) -> None:
        async with sem:
            ch = chunk_by_id[cid]
            red = redact_code(ch["code"])
            sigs = [s for s in state.get("static_signals", []) if s["chunk_client_id"] == cid]
            ctx = await retrieve_for_chunk(red, signal_category=None)
            draft = await refine_chunk(cid, red, sigs, ctx)
            llm_out[cid] = draft

    await asyncio.gather(*(one(cid) for cid in state.get("chunks_for_llm", [])))
    await _emit(
        config,
        StreamEvent(
            event="progress",
            scan_id=state["scan_id"],
            payload={"phase": "rag_llm", "progress": 0.75},
        ),
    )
    return {"llm_outputs": llm_out}


async def node_validate_aggregate(state: AnalysisState, config: RunnableConfig) -> dict[str, Any]:
    session = _session(config)
    merged = validate_and_merge(
        state.get("static_signals", []),
        state.get("llm_outputs", {}),
    )
    final = dedupe_findings(merged)
    tuples = [
        (
            f["file_path"],
            f["line_number"],
            f["vulnerability_type"],
            f["severity"],
            f["confidence"],
            f["source"],
            f["explanation"],
            f["fix"],
        )
        for f in final
    ]
    await scan_repo.add_findings(session, state["scan_id"], tuples)
    for f in final:
        await _emit(
            config,
            StreamEvent(
                event="finding",
                scan_id=state["scan_id"],
                payload=dict(f),
            ),
        )
    await scan_repo.update_scan_status(session, state["scan_id"], status="completed", progress=1.0)
    await _emit(
        config,
        StreamEvent(event="completed", scan_id=state["scan_id"], payload={}),
    )
    return {"validated_findings": final}


def build_graph():
    g = StateGraph(AnalysisState)
    g.add_node("normalize", node_normalize)
    g.add_node("static", node_static)
    g.add_node("risk_select", node_risk_select)
    g.add_node("rag_llm", node_rag_llm)
    g.add_node("validate", node_validate_aggregate)
    g.set_entry_point("normalize")
    g.add_edge("normalize", "static")
    g.add_edge("static", "risk_select")
    g.add_edge("risk_select", "rag_llm")
    g.add_edge("rag_llm", "validate")
    g.add_edge("validate", END)
    return g.compile()
