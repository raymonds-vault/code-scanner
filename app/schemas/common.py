"""Shared schemas."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    type: str


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    database_status: str
    redis_status: str
    pinecone_status: str
