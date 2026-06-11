"""KnowledgeDocument persistence."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_models import KnowledgeDocument


async def create_knowledge_document(
    session: AsyncSession,
    *,
    user_id: str | None,
    source: str,
    category: str,
    doc_version: str,
    namespace: str,
    chunk_count: int,
    path: str | None,
) -> KnowledgeDocument:
    doc = KnowledgeDocument(
        user_id=user_id,
        source=source,
        category=category,
        doc_version=doc_version,
        namespace=namespace,
        chunk_count=chunk_count,
        path=path,
    )
    session.add(doc)
    await session.flush()
    return doc


async def list_knowledge_documents(session: AsyncSession) -> list[KnowledgeDocument]:
    r = await session.execute(
        select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
    )
    return list(r.scalars().all())
