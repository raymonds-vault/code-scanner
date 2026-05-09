#!/usr/bin/env python3
"""Chunk + embed security corpus files and upsert into Pinecone."""

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.pinecone_core import init_pinecone_sync  # noqa: E402
from app.services.analysis.embedding_service import embed_texts  # noqa: E402
from app.services.analysis.vector_stores.guidelines import upsert_guideline_chunks  # noqa: E402
from app.services.knowledge_ingest_service import chunk_text  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=ROOT / "data" / "security_corpus",
    )
    parser.add_argument("--source", type=str, default="local_corpus")
    parser.add_argument("--doc-version", type=str, default="1")
    args = parser.parse_args()

    get_settings()
    init_pinecone_sync()

    texts: list[str] = []
    payloads: list[dict] = []
    for path in sorted(args.corpus_dir.glob("**/*")):
        if not path.is_file() or path.suffix.lower() not in (".md", ".txt"):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        category = path.stem.lower().replace(" ", "_")
        for idx, chunk in enumerate(chunk_text(raw)):
            texts.append(chunk)
            payloads.append(
                {
                    "source": args.source,
                    "category": category,
                    "doc_version": args.doc_version,
                    "ingested_at": "",
                    "path": str(path.relative_to(args.corpus_dir)),
                    "chunk_index": idx,
                    "content_hash": hashlib.sha256(chunk.encode()).hexdigest()[:16],
                }
            )
    if not texts:
        print("No corpus files found.", file=sys.stderr)
        sys.exit(1)
    vectors = embed_texts(texts)
    upsert_guideline_chunks(vectors, texts, payloads)
    print(f"Ingested {len(texts)} chunks into Pinecone")


if __name__ == "__main__":
    main()
