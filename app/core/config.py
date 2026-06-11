"""Application settings from environment."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "code-scanner"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+asyncpg://code-scanner:code-scanner@localhost:5433/code-scanner"
    )

    REDIS_URL: str = "redis://localhost:6380/0"
    REDIS_ENABLED: bool = True

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "security-guidelines"
    PINECONE_NAMESPACE: str = "security"
    PINECONE_HOST: str = ""

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384
    EMBEDDING_BACKEND: str = "huggingface"
    LLM_MODEL: str = "microsoft/phi-2"
    # stub | transformers | hf_inference | groq | openai | routed
    LLM_BACKEND: str = "stub"
    LLM_MAX_NEW_TOKENS: int = 256
    MODEL_ROUTING_POLICY: str = "balanced"
    MODEL_SPEED_PREFERENCE: str = "balanced"
    MODEL_QUALITY_GATE: float = 0.7
    MODEL_FALLBACK_ORDER: str = "groq,openai,hf_inference,transformers,stub"
    # Cloud inference: https://huggingface.co/docs/api-inference (Hub token works)
    HF_TOKEN: str = Field(
        default="",
        validation_alias=AliasChoices("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGINGFACE_API_KEY"),
    )
    HF_INFERENCE_BASE_URL: str = "https://api-inference.huggingface.co"
    HF_EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    RISK_THRESHOLD: float = 0.35
    MAX_LLM_CHUNKS: int = 20
    MAX_CONCURRENCY: int = 4
    SCAN_MODE: str = "local_only"

    GOOGLE_CLIENT_ID: str = ""
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
