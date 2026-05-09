"""Lazy Hugging Face sentence-transformers embeddings."""

from functools import lru_cache

import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_model = None


def _load_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "sentence-transformers is required for embeddings. "
                "Install: pip install -r requirements-ml.txt"
            ) from e

        settings = get_settings()
        if settings.EMBEDDING_BACKEND.lower() != "huggingface":
            raise RuntimeError(f"Unsupported EMBEDDING_BACKEND={settings.EMBEDDING_BACKEND!r}")
        model_id = settings.HF_EMBEDDING_MODEL or settings.EMBEDDING_MODEL
        logger.info("Loading embedding model %s", model_id)
        _model = SentenceTransformer(model_id)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _load_model()
    vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    if isinstance(vectors, np.ndarray):
        return vectors.tolist()
    return [v.tolist() for v in vectors]


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]
