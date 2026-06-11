"""Knowledge upload API."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_optional_user
from app.core.config import get_settings
from app.core.dependencies import get_db
from app.repositories.knowledge_doc_repo import create_knowledge_document, list_knowledge_documents
from app.schemas.knowledge import (
    KnowledgeDocumentListResponse,
    KnowledgeDocumentOut,
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


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(db: AsyncSession = Depends(get_db)) -> KnowledgeDocumentListResponse:
    docs = await list_knowledge_documents(db)
    return KnowledgeDocumentListResponse(
        documents=[
            KnowledgeDocumentOut(
                id=d.id,
                source=d.source,
                category=d.category,
                doc_version=d.doc_version,
                namespace=d.namespace,
                chunk_count=d.chunk_count,
                path=d.path,
                created_at=d.created_at,
            )
            for d in docs
        ],
        total=len(docs),
    )


@router.post("/documents", response_model=KnowledgeIngestResponse)
async def upload_document(
    body: KnowledgeDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
) -> KnowledgeIngestResponse:
    try:
        result = await run_in_threadpool(
            ingest_knowledge_text,
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

    await create_knowledge_document(
        db,
        user_id=current_user["sub"] if current_user else None,
        source=result["source"],
        category=result["category"],
        doc_version=result["doc_version"],
        namespace=result["namespace"],
        chunk_count=result["chunk_count"],
        path=None,
    )
    await db.commit()
    return KnowledgeIngestResponse(**result)


@router.post("/files", response_model=KnowledgeIngestResponse)
async def upload_file(
    file: UploadFile = File(...),
    source: str = Form(...),
    category: str = Form(...),
    doc_version: str = Form("1"),
    namespace: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict | None = Depends(get_optional_user),
) -> KnowledgeIngestResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_KNOWLEDGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    raw = await file.read()
    text = raw.decode("utf-8", errors="replace")
    try:
        result = await run_in_threadpool(
            ingest_knowledge_text,
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

    await create_knowledge_document(
        db,
        user_id=current_user["sub"] if current_user else None,
        source=result["source"],
        category=result["category"],
        doc_version=result["doc_version"],
        namespace=result["namespace"],
        chunk_count=result["chunk_count"],
        path=file.filename,
    )
    await db.commit()
    return KnowledgeIngestResponse(**result)
