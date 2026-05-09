"""Knowledge upload and ingestion schemas."""

from pydantic import BaseModel, Field


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
