# Shield — AI-Powered Code Security Analysis Engine

**Version:** 0.3.0

Shield is a production-grade REST API for automated security vulnerability detection in source code. It combines deterministic static analysis with LLM-assisted refinement and Retrieval-Augmented Generation (RAG) over a security knowledge base, delivering findings with severity ratings, confidence scores, and fix suggestions in real time via WebSocket streaming.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Analysis Pipeline](#analysis-pipeline)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Getting Started](#getting-started)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Development](#local-development)
- [Database Migrations](#database-migrations)
- [CLI Client](#cli-client)
- [Scripts](#scripts)
- [Testing](#testing)
- [Changelog](#changelog)

---

## Features

- **Static analysis** — regex-based detection of SQL injection, command execution, and path traversal patterns
- **Risk-gated LLM refinement** — only high-risk chunks are sent to an LLM, keeping costs low
- **RAG-augmented context** — Pinecone vector search retrieves relevant security guidelines before each LLM call
- **Multi-provider LLM routing** — OpenAI, Groq, Hugging Face Inference API, local transformers, and a deterministic stub; configurable fallback chain
- **Real-time streaming** — WebSocket endpoint pushes incremental findings as analysis progresses
- **Knowledge ingestion** — REST endpoints and a script to load security corpus documents into Pinecone
- **Secret redaction** — API keys and tokens stripped from code before embedding or LLM submission
- **Async-first** — asyncpg, SQLAlchemy async, concurrent LLM calls
- **TypeScript CLI** — thin Node.js client for submitting local files and streaming results

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.115+ |
| Analysis orchestration | LangGraph 0.2+ / LangChain Core 0.3+ |
| Database ORM | SQLAlchemy 2.0 async + asyncpg |
| Database | PostgreSQL 16 |
| Cache / pub-sub | Redis 7 (optional) |
| Vector store | Pinecone |
| Embeddings | sentence-transformers (BAAI/bge-small-en-v1.5) |
| LLM providers | OpenAI, Groq, Hugging Face, local transformers |
| Migrations | Alembic 1.13+ |
| Runtime | Python 3.12, Uvicorn |
| Container | Docker + Docker Compose |
| CLI | TypeScript / Node.js |
| Testing | pytest + pytest-asyncio |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Clients                              │
│        REST (HTTP)           WebSocket stream               │
│   POST /api/v1/scan      WS /api/v1/scan/{id}/stream       │
└────────────┬─────────────────────────┬──────────────────────┘
             │                         │
             ▼                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI App                            │
│   scan_controller   knowledge_controller   health_controller│
│                 scan_events (pub/sub broker)                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│               LangGraph Analysis Pipeline                   │
│                                                             │
│  normalize → static → risk_select → rag_llm → validate     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ static       │  │ rag_llm      │  │ validate_aggregate│  │
│  │ _analyzer.py │  │ retrieval +  │  │ merge, dedupe,   │  │
│  │ regex patterns│  │ LLM refiner  │  │ confidence gate  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└──────┬──────────────────────┬──────────────────────────────┘
       │                      │
       ▼                      ▼
┌─────────────┐    ┌──────────────────────────────────────────┐
│ PostgreSQL  │    │              External Services            │
│             │    │  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│ scans       │    │  │ Pinecone │  │  OpenAI  │  │  Groq  │  │
│ scan_chunks │    │  │ (vectors)│  │   API    │  │  API   │  │
│ static_     │    │  └──────────┘  └──────────┘  └────────┘  │
│  signals    │    │  ┌──────────┐  ┌────────────────────────┐ │
│ findings    │    │  │  Redis   │  │ HuggingFace / local    │ │
└─────────────┘    │  │ (cache)  │  │ transformers           │ │
                   │  └──────────┘  └────────────────────────┘ │
                   └──────────────────────────────────────────┘
```

---

## Project Structure

```
shield/
├── app/
│   ├── main.py                          # FastAPI app factory + lifespan
│   ├── core/
│   │   ├── config.py                    # Pydantic-settings (all env vars)
│   │   ├── database.py                  # Async SQLAlchemy engine + session
│   │   ├── redis_client.py              # Redis lifecycle
│   │   ├── pinecone_core.py             # Pinecone client init
│   │   ├── logging.py                   # Structured logging setup
│   │   ├── exceptions.py                # Global exception handlers
│   │   └── dependencies.py              # FastAPI dependency injection
│   ├── models/
│   │   ├── base.py                      # Base, TimestampMixin, UUIDMixin
│   │   └── scan_models.py               # Scan, ScanChunk, StaticSignal, Finding
│   ├── schemas/
│   │   ├── common.py                    # HealthResponse, ErrorResponse, PaginationParams
│   │   ├── scan.py                      # ScanRequest, ScanCreatedResponse, FindingOut, StreamEvent
│   │   └── knowledge.py                 # KnowledgeDocumentRequest, KnowledgeIngestResponse
│   ├── controllers/
│   │   ├── health_controller.py         # GET /health
│   │   ├── scan_controller.py           # Scan CRUD + WebSocket stream
│   │   └── knowledge_controller.py      # Knowledge ingestion endpoints
│   ├── repositories/
│   │   ├── scan_repo.py                 # Scan / chunk / finding / signal CRUD
│   │   └── pinecone_repo.py             # Pinecone vector operations
│   └── services/
│       ├── scan_service.py              # Scan lifecycle, graph execution
│       ├── scan_events.py               # In-memory WebSocket pub/sub broker
│       ├── knowledge_ingest_service.py  # Chunk → embed → Pinecone upsert
│       └── analysis/
│           ├── graph.py                 # LangGraph pipeline builder
│           ├── state.py                 # AnalysisState schema
│           ├── types.py                 # Typed dicts (CodeChunkState, FindingDict, …)
│           ├── static_analyzer.py       # Regex pattern detection
│           ├── risk_engine.py           # Chunk risk scoring
│           ├── embedding_service.py     # Lazy-loaded sentence-transformers
│           ├── retrieval_service.py     # RAG retrieval from Pinecone
│           ├── llm_refinement.py        # Single LLM call entry point
│           ├── redaction.py             # Secret/token redaction
│           ├── validation_engine.py     # Merge + confidence gating
│           ├── aggregation.py           # Finding deduplication
│           ├── llm_providers/
│           │   ├── router.py            # Multi-provider routing + fallback
│           │   ├── stub.py              # Deterministic stub (offline/tests)
│           │   ├── openai_compatible.py # OpenAI + Groq
│           │   ├── huggingface.py       # HF Inference API + local transformers
│           │   └── common.py            # Shared prompt builder, JSON parser
│           └── vector_stores/
│               └── guidelines.py        # Pinecone facade
├── alembic/
│   └── versions/
│       └── 001_initial_scans.py         # Initial schema migration
├── changelogs/                          # Per-version release notes
├── cli/
│   └── src/scan.ts                      # TypeScript CLI client
├── data/                                # Security corpus (markdown / text)
├── scripts/
│   ├── ingest_security_corpus.py        # Bulk corpus ingestion to Pinecone
│   ├── run_with_debugpy.py              # Debug server (attaches IDE debugger)
│   └── agent_changelog_workflow.sh      # Changelog/version helper
├── tests/                               # pytest suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt                     # Core dependencies
├── requirements-ml.txt                  # ML dependencies (torch, sentence-transformers)
├── requirements-dev.txt                 # Dev dependencies (debugpy)
├── alembic.ini
├── pytest.ini
└── version.properties
```

---

## Analysis Pipeline

The analysis runs as a 5-node **LangGraph** sequential graph (`app/services/analysis/graph.py`):

```
normalize → static → risk_select → rag_llm → validate_aggregate
```

### 1. `normalize`
Initialises `AnalysisState`, emits a `progress` WebSocket event.

### 2. `static`
Runs regex patterns on every chunk:

| Pattern | Detects |
|---|---|
| SQL injection | `cursor.execute` / `.execute` with string formatting or concatenation |
| Command execution | `subprocess`, `os.system`, `eval` |
| Path traversal | `open(` / `Path().read` involving user-controlled input |

Each match becomes a `StaticSignal` row and a `static_signal` WebSocket event.

### 3. `risk_select`
Scores every chunk 0–1 across three factors:

| Factor | Weight | Signal |
|---|---|---|
| Pattern confidence | 45% | Static signal confidence |
| Sensitive keywords | 25% | `password`, `token`, `api_key`, `secret` in code |
| Input flow | 20% | `request`, `input`, `argv`, `getparameter` in code |

Chunks below `RISK_THRESHOLD` (default 0.35) skip the LLM. At most `MAX_LLM_CHUNKS` (default 20) are forwarded.

### 4. `rag_llm`
For each selected chunk (up to `MAX_CONCURRENCY` = 4 concurrent):
1. **Redact** — strip API keys, tokens, passwords from code
2. **Retrieve** — embed redacted code, search Pinecone (top-5), return `related_patterns`, `similar_code`, `vulnerability_docs`
3. **Refine** — call the configured LLM provider with signals + RAG context + redacted code
4. Emit `finding` or `llm_skipped` WebSocket event

### 5. `validate_aggregate`
- Merges static signals and LLM findings
- Deduplicates by `(file_path, line, vulnerability_type)`
- Applies confidence gates:
  - LLM-only findings with confidence < 0.6 are downgraded
  - Findings where LLM type ≠ static type and confidence < 0.85 are downgraded
- Saves final `Finding` rows to PostgreSQL
- Emits `completed` WebSocket event

---

## API Reference

### Health

#### `GET /health`
Returns service health across all dependencies.

**Response:**
```json
{
  "status": "healthy",
  "database_status": "connected",
  "redis_status": "connected",
  "pinecone_status": "connected",
  "app_name": "code-scanner"
}
```

---

### Scans

#### `POST /api/v1/scan`
Submit code chunks for analysis. Returns immediately; analysis runs asynchronously.

**Request body:**
```json
{
  "chunks": [
    {
      "chunk_id": "unique-id",
      "file_path": "src/api/users.py",
      "start_line": 42,
      "end_line": 60,
      "code": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
      "language": "python",
      "context_summary": "User lookup endpoint",
      "dependencies": []
    }
  ],
  "metadata": {
    "repo": "my-service",
    "branch": "main"
  },
  "client_request_id": "optional-idempotency-key"
}
```

**Response `202`:**
```json
{ "id": "uuid", "status": "pending" }
```

---

#### `GET /api/v1/scan/{scan_id}`
Poll scan status and retrieve findings.

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "progress": 1.0,
  "metadata": {},
  "findings": [
    {
      "id": "uuid",
      "file_path": "src/api/users.py",
      "line_number": 43,
      "vulnerability_type": "sql_injection",
      "severity": "high",
      "confidence": 0.92,
      "source": "hybrid",
      "explanation": "User-controlled input interpolated directly into SQL string.",
      "fix": "Use parameterised queries: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))"
    }
  ]
}
```

---

#### `WS /api/v1/scan/{scan_id}/stream`
WebSocket endpoint. Connect immediately after `POST /api/v1/scan` to receive real-time events.

**Event types:**

| Event | Payload |
|---|---|
| `progress` | `{ progress: float }` |
| `chunk_started` | `{ chunk_id: str }` |
| `static_signal` | `{ chunk_id, signal_type, confidence, location }` |
| `llm_skipped` | `{ chunk_id, reason }` |
| `finding` | full finding object |
| `error` | `{ message: str }` |
| `completed` | `{ total_findings: int }` |

---

### Knowledge

#### `GET /api/v1/knowledge/status`
Returns the current knowledge base configuration.

**Response:**
```json
{
  "pinecone_index": "code-scan",
  "pinecone_namespace": "security",
  "embedding_backend": "huggingface",
  "embedding_model": "BAAI/bge-small-en-v1.5"
}
```

---

#### `POST /api/v1/knowledge/documents`
Ingest a security document as plain text.

**Request body:**
```json
{
  "source": "owasp-top10",
  "category": "injection",
  "text": "SQL injection occurs when...",
  "doc_version": "2021",
  "namespace": "security"
}
```

---

#### `POST /api/v1/knowledge/files`
Upload a `.md` or `.txt` file for ingestion (multipart form-data).

---

## Configuration

All settings are read from environment variables (or `.env`). Copy `.env.example` to `.env` and fill in your values.

### Core

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `code-scanner` | Application name in health responses |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Database

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Async PostgreSQL URL (`postgresql+asyncpg://...`) |

### Redis

| Variable | Default | Description |
|---|---|---|
| `REDIS_ENABLED` | `true` | Enable Redis connection |
| `REDIS_URL` | — | Redis connection URL |

### Pinecone

| Variable | Required | Description |
|---|---|---|
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | `code-scan` | Index name |
| `PINECONE_NAMESPACE` | `security` | Vector namespace |
| `PINECONE_HOST` | — | Optional; overrides index name lookup |

### Embeddings

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_BACKEND` | `huggingface` | Embedding provider |
| `HF_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Model for local/HF embeddings |
| `HF_TOKEN` | — | Hugging Face Hub token (aliases: `HUGGINGFACE_HUB_TOKEN`, `HUGGINGFACE_API_KEY`) |
| `HF_INFERENCE_BASE_URL` | `https://api-inference.huggingface.co` | HF Inference API base URL |

### LLM Routing

| Variable | Default | Options | Description |
|---|---|---|---|
| `LLM_BACKEND` | `stub` | `stub`, `openai`, `groq`, `hf_inference`, `transformers`, `routed` | Active LLM backend |
| `LLM_MODEL` | `microsoft/phi-2` | any HF model ID | Local transformers model |
| `MODEL_ROUTING_POLICY` | `balanced` | `balanced`, `quality`, `speed` | Provider selection strategy |
| `MODEL_QUALITY_GATE` | `0.7` | 0–1 | Minimum provider quality score |
| `MODEL_FALLBACK_ORDER` | `groq,openai,hf_inference,transformers,stub` | — | Ordered fallback chain |

### LLM Provider Keys

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | Model name (default: `gpt-4o-mini`) |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Model name (default: `llama-3.1-8b-instant`) |

### Analysis Tuning

| Variable | Default | Description |
|---|---|---|
| `RISK_THRESHOLD` | `0.35` | Chunks below this skip LLM analysis |
| `MAX_LLM_CHUNKS` | `20` | Max chunks forwarded to LLM per scan |
| `MAX_CONCURRENCY` | `4` | Concurrent LLM calls |

### Debugging

| Variable | Default | Description |
|---|---|---|
| `DEBUGPY_HOST` | `127.0.0.1` | debugpy listen host |
| `DEBUGPY_PORT` | `5678` | debugpy listen port |

---

## Getting Started

### Docker (Recommended)

**Prerequisites:** Docker, Docker Compose v2

```bash
# 1. Clone and enter the repo
git clone <repo-url> shield && cd shield

# 2. Copy and configure environment
cp .env.example .env
# Edit .env — minimum required: PINECONE_API_KEY, DATABASE_URL (pre-filled for Docker)

# 3. Build and start all services
docker compose up -d --build

# 4. Check logs
docker compose logs -f api
```

Services started:

| Service | Host port | Description |
|---|---|---|
| `api` | 8000 | Shield FastAPI app |
| `postgres` | 5433 | PostgreSQL 16 |
| `redis` | 6380 | Redis 7 |
| `qdrant` | 6333 / 6334 | Qdrant (legacy; not used by app) |

The `api` container automatically runs `alembic upgrade head` before starting Uvicorn.

The API will be available at `http://localhost:8000`. Check health at `http://localhost:8000/health`.

---

### Local Development

**Prerequisites:** Python 3.12, PostgreSQL, Redis (or use Docker for services only)

```bash
# Start infrastructure only
docker compose up -d postgres redis

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# For ML/embedding support:
pip install -r requirements-ml.txt
# For debugging:
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to localhost:5433

# Run migrations
alembic upgrade head

# Start the app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**With IDE debugger (VS Code / Cursor):**
```bash
python scripts/run_with_debugpy.py
# Waits for debugger to attach on port 5678
```

---

## Database Migrations

Migrations are managed with Alembic.

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Generate a new migration from model changes
alembic revision --autogenerate -m "description"

# View migration history
alembic history
```

**Schema summary:**

| Table | Description |
|---|---|
| `scans` | Top-level scan record (status, progress, metadata) |
| `scan_chunks` | Code segments submitted for analysis |
| `static_signals` | Regex pattern matches per chunk |
| `findings` | Final security findings per scan |

---

## CLI Client

A TypeScript CLI is provided for submitting local files directly from the command line.

```bash
cd cli
npm install
npm run build

# Scan a file or directory
node dist/scan.js <path-to-file-or-directory> [api-base-url]

# Default api-base-url is http://localhost:8000
node dist/scan.js ./src
node dist/scan.js ./src https://my-shield-instance.example.com
```

The CLI discovers all source files (skipping `.git`, `node_modules`, and binaries), submits them in a single scan request, then streams WebSocket events to stdout until the scan completes.

**Supported languages:** Python, TypeScript, JavaScript, Go, Java, Rust

---

## Scripts

### `scripts/ingest_security_corpus.py`

Bulk-ingest a directory of markdown/text security documents into Pinecone.

```bash
python scripts/ingest_security_corpus.py \
  --corpus-dir data/ \
  --source owasp-top10 \
  --doc-version 2021
```

Requires ML dependencies (`requirements-ml.txt`) and a valid `PINECONE_API_KEY` in `.env`.

---

### `scripts/run_with_debugpy.py`

Starts Uvicorn with debugpy listening on port 5678 and pauses until an IDE debugger attaches.

```bash
python scripts/run_with_debugpy.py
```

Configure via `.env`:
- `DEBUGPY_HOST` (default: `127.0.0.1`)
- `DEBUGPY_PORT` (default: `5678`)

---

### `scripts/agent_changelog_workflow.sh`

Prints the changelog and version management workflow.

```bash
# Show workflow instructions
./scripts/agent_changelog_workflow.sh

# Verify current version matches latest changelog entry
./scripts/agent_changelog_workflow.sh --verify
```

---

## Testing

Tests use SQLite (no Postgres required), mock Pinecone, and disable Redis.

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a specific test module
python3 -m pytest tests/test_api.py -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=term-missing
```

**Test modules:**

| Module | Coverage |
|---|---|
| `test_api.py` | Scan CRUD endpoints |
| `test_knowledge_api.py` | Knowledge ingestion endpoints |
| `test_validation.py` | Validation engine + confidence gating |
| `test_vector_store.py` | Pinecone facade operations |
| `test_risk.py` | Risk scoring |
| `test_model_routing.py` | LLM provider routing and fallback |
| `conftest.py` | Shared fixtures, Pinecone mocking |

---

## Changelog

### v0.3.0
- Removed Qdrant entirely; committed exclusively to Pinecone as the vector store
- Improved test isolation: Pinecone client fully mocked, Redis disabled in test fixtures
- Dockerfile added; `docker compose up --build` now starts the full stack
- `alembic upgrade head` runs automatically on container startup

### v0.2.0
- Multi-provider LLM routing with configurable fallback chain (`groq`, `openai`, `hf_inference`, `transformers`, `stub`)
- Pinecone RAG integration: security knowledge retrieved per-chunk before LLM refinement
- Knowledge ingestion REST API (`POST /api/v1/knowledge/documents`, `POST /api/v1/knowledge/files`)
- Secret redaction applied before embedding and LLM submission
- `MODEL_ROUTING_POLICY`, `MODEL_QUALITY_GATE`, `MODEL_FALLBACK_ORDER` configuration options
- `ingest_security_corpus.py` script for bulk corpus loading

### v0.1.4
- Added `debugpy` integration (`scripts/run_with_debugpy.py`)
- VS Code / Cursor launch configurations

### v0.1.3
- Added Cursor rules for API and CLI test conventions

### v0.1.2
- Added Cursor rules for changelog and version management workflow

### v0.1.1
- Added Hugging Face Inference API as an LLM provider
- `HF_TOKEN` / `HF_INFERENCE_BASE_URL` configuration

### v0.1.0
- Initial release
- FastAPI application with LangGraph 5-node analysis pipeline
- PostgreSQL schema: `scans`, `scan_chunks`, `static_signals`, `findings`
- Static analysis: SQL injection, command execution, path traversal
- WebSocket streaming of analysis events
- Qdrant vector store integration (later replaced by Pinecone)
- TypeScript CLI client

### v0.0.0
- Project scaffold
