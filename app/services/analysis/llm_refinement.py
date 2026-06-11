"""Single LLM call site: refinement / explanation only (not primary detection)."""

from app.services.analysis.llm_providers.router import refine_with_router
from app.services.analysis.types import ContextBundleDict, LlmDraftDict, StaticSignalDict


async def refine_chunk(
    chunk_id: str,
    redacted_code: str,
    signals: list[StaticSignalDict],
    context: ContextBundleDict,
) -> LlmDraftDict:
    return await refine_with_router(chunk_id, redacted_code, signals, context)
