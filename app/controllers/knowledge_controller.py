"""Knowledge upload API."""

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.knowledge import (
    KnowledgeDocumentRequest,
    KnowledgeIngestResponse,
    KnowledgeStatusResponse,
)
from app.services.knowledge_ingest_service import (
    SUPPORTED_KNOWLEDGE_SUFFIXES,
    ingest_knowledge_text,
)

router = APIRouter(tags=["Knowledge"], prefix="/knowledge")


@router.get("/status", response_model=KnowledgeStatusResponse)
async def knowledge_status() -> KnowledgeStatusResponse:
    settings = get_settings()
    return KnowledgeStatusResponse(
        pinecone_index=settings.PINECONE_INDEX_NAME,
        pinecone_namespace=settings.PINECONE_NAMESPACE,
        embedding_backend=settings.EMBEDDING_BACKEND,
        embedding_model=settings.HF_EMBEDDING_MODEL or settings.EMBEDDING_MODEL,
    )


@router.post("/documents", response_model=KnowledgeIngestResponse)
async def upload_document(body: KnowledgeDocumentRequest) -> KnowledgeIngestResponse:
    try:
        result = ingest_knowledge_text(
            source=body.source,
            category=body.category,
            text=body.text,
            doc_version=body.doc_version,
            namespace=body.namespace,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return KnowledgeIngestResponse(**result)


@router.post("/files", response_model=KnowledgeIngestResponse)
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form(...),
    category: str = Form(...),
    doc_version: str = Form("1"),
    namespace: str | None = Form(None),
) -> KnowledgeIngestResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_KNOWLEDGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    raw = await file.read()
    text = raw.decode("utf-8", errors="replace")
    try:
        result = ingest_knowledge_text(
            source=source,
            category=category,
            text=text,
            doc_version=doc_version,
            namespace=namespace,
            path=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return KnowledgeIngestResponse(**result)
