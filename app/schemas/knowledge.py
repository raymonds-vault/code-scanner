"""Knowledge upload and ingestion schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeDocumentOut(BaseModel):
    id: str
    source: str
    category: str
    doc_version: str
    namespace: str
    chunk_count: int
    path: str | None
    created_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    documents: list[KnowledgeDocumentOut]
    total: int


class KnowledgeDocumentRequest(BaseModel):
    source: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1)
    doc_version: str = Field(default="1", min_length=1, max_length=100)
    namespace: str | None = Field(default=None, max_length=100)


class KnowledgeIngestResponse(BaseModel):
    source: str
    category: str
    doc_version: str
    namespace: str
    embedding_model: str
    chunk_count: int
    content_hashes: list[str]


class KnowledgeStatusResponse(BaseModel):
    pinecone_index: str
    pinecone_namespace: str
    embedding_backend: str
    embedding_model: str
