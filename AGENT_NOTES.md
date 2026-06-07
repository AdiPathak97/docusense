# AGENT_NOTES.md — DocuSense Session Log

> Read this before acting in any session.
> Append-only. Do not delete old entries — the history is the value.
> For stable architecture, see CLAUDE.md.

---

## How to Use

- **Before starting**: read the latest entry to understand current state
- **After completing work**: add a dated entry summarising what changed and what's pending
- **Non-obvious decisions**: record here with reasoning; if architectural, also update CLAUDE.md

---

## [Project Init — Skeleton]

**Status**: Full project skeleton scaffolded. No node logic implemented yet.

**What exists (runnable skeleton):**
- `config.py` — pydantic-settings, all env vars
- `services/llm_provider.py` — full provider abstraction (Claude, AzureOpenAI, OpenAI, Mock)
- `agent/state.py` — AgentState TypedDict
- `agent/prompts.py` — GRADE, GENERATE, REWRITE prompts with inline tuning notes
- `agent/graph.py` — LangGraph StateGraph wired (calls nodes via functools.partial)
- `agent/nodes.py` — `grade_docs` and `generate` fully implemented; `retrieve` is a stub
- `services/vector_store.py` — upsert implemented; `query()` is a stub
- `services/ingestion.py` — pipeline structure + chunk loop implemented; `parse_document` and `chunk_pages` are stubs
- `models/` — SQLAlchemy ORM models complete
- `db/base.py` — async engine + get_db() complete
- `dependencies.py` — DI singletons complete
- `api/documents.py` — route signatures + TODOs; logic not implemented
- `api/chat.py` — route signature + TODO; logic not implemented
- `main.py` — FastAPI app, routers registered, startup hook
- `docker-compose.yml`, `Dockerfile.backend`, `requirements.txt`, `.env.example` — complete
- Frontend — package.json + file stubs only

**Phase 1 TODOs (implement to get first end-to-end upload working):**
- [x] `services/ingestion.py` → `parse_document()`: pypdfium2 + python-docx + plain text
- [x] `services/ingestion.py` → `chunk_pages()`: RecursiveCharacterTextSplitter with tiktoken
- [x] `services/vector_store.py` → `query()`: per-collection query, merge + sort by distance
- [x] `api/documents.py` → `upload_document()`: save temp file, create DB record, background ingest
- [x] `api/documents.py` → `list_documents()`, `delete_document()`
- [x] Alembic migration files written manually (`alembic.ini`, `backend/db/migrations/`)

**Phase 2 TODOs (get first end-to-end query working):**
- [ ] `agent/nodes.py` → `retrieve()`: embed question, call vector_store.query()
- [ ] `api/chat.py` → `query()`: session resolution, graph invocation, DB persistence

**Phase 3 TODOs:**
- [ ] Frontend: Upload.tsx, Chat.tsx, SourceCard.tsx, client.ts

**Key decisions made:**
- Claude is primary LLM_PROVIDER; embeddings use OpenAI (Claude has no embeddings API)
- Chat and embedding are separate protocols for this reason — see CLAUDE.md §3.3
- `grade_docs` node calls LLM once per chunk (not batched). Parallelise with asyncio.gather
  if per-query latency is unacceptable in testing.
- `rewrite_query` prompt written and in prompts.py but NOT wired into graph yet (v2)
- Frontend stubs only — iterate Phase 3 after backend is end-to-end

**Open questions:**
- Citation parsing in SourceCard.tsx — regex on `[filename, p.N]` pattern or structured response?
- Alembic migration testing — `alembic` only exists inside Docker, not locally. `main.py` startup hook
  runs `create_all` which pre-creates tables, so `alembic upgrade head` will conflict on an existing DB.
  Decision needed: remove `create_all` from startup and rely on Alembic in deploy step, or keep `create_all`
  for dev and use `alembic stamp head` to sync state on existing DBs. Test path: wipe postgres volume,
  run `docker compose run --rm backend alembic upgrade head` before starting the backend.

---

## [Phase 1 — Document Upload & Ingestion]

**Status**: Complete and verified end-to-end.

**What was implemented:**
- `parse_document()` — pypdfium2 (PDF), python-docx (DOCX), plain text. Per-page extraction.
- `chunk_pages()` — RecursiveCharacterTextSplitter, 500 tokens / 50 overlap, tracks page_number per chunk.
- `ingest()` return type changed from `int` to `list[dict]` — returns `{id, chunk_index, page_number}` per chunk so the API can persist accurate Postgres Chunk rows with correct page numbers and matching IDs to ChromaDB.
- `VectorStoreClient.query()` — queries each `doc_{uuid}` collection, merges, sorts by distance ascending, returns top-k.
- `upload_document()` — 202 response, Document row (status=processing), background task with its own AsyncSession.
- `list_documents()`, `delete_document()` — standard CRUD; delete cascades in Postgres and drops ChromaDB collection.
- Alembic files written manually (alembic.ini, env.py, script.py.mako, versions/0001). `main.py` startup hook runs `create_all` for Docker dev, so Alembic is for production migrations.

**Bugs fixed during implementation:**
- `chromadb.AsyncHttpClient()` is an async factory (must be awaited) — fixed with lazy `_get_client()` method.
- Background task was silently swallowing exceptions — added `logger.exception()` so full tracebacks appear in Docker logs.
- PDF word-joining issue with pypdf — switched to pypdfium2 (Google PDFium engine, 97% quality benchmark, 35× faster, Apache 2.0 license). pdfplumber was rejected: slower and lower quality per py-pdf/benchmarks.

**Key decisions:**
- Chunk IDs are generated in `ingest()` and reused as Postgres Chunk PKs — ChromaDB and Postgres refer to the same chunk by the same UUID.
- `VectorStoreClient` uses lazy async init (`_get_client`) because `AsyncHttpClient` must be awaited and `__init__` cannot be async. The `lru_cache` singleton in `dependencies.py` means this initialises once.
- Alembic `env.py` uses the asyncpg URL directly (no driver swap needed for async alembic pattern).
