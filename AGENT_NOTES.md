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

---

## [Logging & Error Handling]

**Status**: Complete. All backend layers have structured logging and typed error handling.

**What was implemented:**
- `backend/exceptions.py` (new) — `DocuSenseError` base + `IngestionError`, `VectorStoreError`, `LLMError`, `AgentError` subclasses with typed context fields
- `backend/logging_config.py` (new) — `configure_logging(log_level, log_format)` via `dictConfig`. Root logger always `WARNING`; `backend.*` driven by `LOG_LEVEL` env var. Stdlib-only JSON formatter opt-in via `LOG_FORMAT=json`
- `main.py` — `configure_logging()` called first; `request_id` middleware using `contextvars.ContextVar` + `logging.Filter`; global exception handlers for `DocuSenseError` (clean JSON, no traceback) and `Exception` (safe message + full traceback); DB startup guard with `sys.exit(1)`
- `services/llm_provider.py` — all 5 API methods wrapped → `LLMError from exc`; factory functions raise `LLMError` instead of `ValueError`; mock warning added to both `get_chat_provider` and `get_embedding_provider`
- `services/vector_store.py` — all 4 operations wrapped → `VectorStoreError from exc`; silent `except: pass` replaced with logged WARNING
- `services/ingestion.py` — `parse_document`, `chunk_pages`, per-chunk embedding wrapped → typed errors; INFO at start/end, DEBUG for page/chunk counts
- `agent/nodes.py` — `grade_docs` catches `LLMError` per-chunk and continues (graceful degradation); `generate` raises `AgentError` on failure
- `dependencies.py` — `LLMError` caught at provider init with CRITICAL log
- `db/base.py` — DEBUG on engine creation; session error logged before re-raise
- `api/documents.py` — split `except Exception` into `DocuSenseError` (clean one-line ERROR) and `Exception` (full traceback); silent delete swallow → logged WARNING
- `config.py`, `.env.example` — `LOG_LEVEL` and `LOG_FORMAT` fields added
- `docker-compose.yml` — `json-file` logging driver with 10 MB × 3 rotation on backend service
- `CLAUDE.md §5` — `LOG_LEVEL` and `LOG_FORMAT` rows added to env vars table

**Bugs encountered and resolved:**
1. `pypdfium2` UserWarning in logs — `warnings.warn()` is separate from `logging`; fixed with `warnings.filterwarnings()` in `configure_logging()`
2. Mock warning not firing on upload — upload only injects `get_embedding_provider_dep()`, not chat provider; added mock warning to `get_embedding_provider()` too
3. Traceback visible for handled `LLMError` — `logger.exception()` always logs the full chain; fixed by splitting catch into `DocuSenseError` (no traceback, message is self-describing) vs `Exception` (full traceback for unknowns). Applied this rule globally: `DocuSenseError` handler in `main.py` also had `exc_info=True` removed

**Key decisions:**
- Rule: typed `DocuSenseError` → `logger.error()` no traceback; bare `Exception` → `logger.exception()` or `exc_info=True`
- `warnings` module vs `logging` module are entirely separate systems; only `configure_logging()` knows about both
- No file handler — stdout only, Docker `json-file` driver handles rotation and persistence
- `LOG_LEVEL` and `LOG_FORMAT` go in `CLAUDE.md §5` (not AGENT_NOTES) because they are permanent operational knobs a fresh agent must know about
- Docker Desktop Restart does NOT re-read `.env` / `env_file` — only `docker-compose up` does. This is Docker behaviour, not a code issue.

---

## [Phase 2 — Query Pipeline, Rewrite Loop & Frontend]

**Status**: Complete.

**What was implemented:**

### Backend

- `agent/state.py` — Added `rewrite_count: int` field to `AgentState` to cap the query-rewrite loop.
- `agent/nodes.py` — `retrieve()` fully implemented: embeds question via `EmbeddingProvider`, queries ChromaDB via `VectorStoreClient.query()`, maps raw results to `list[DocumentChunk]`. Also added new `rewrite_query()` node: calls `REWRITE_SYSTEM/REWRITE_USER` prompt, returns reformulated question + incremented `rewrite_count` + cleared chunk lists so `retrieve` starts fresh.
- `agent/graph.py` — Rewritten for v2 topology. `build_graph()` now accepts `embedding_provider`. Added `rewrite_query` node. Replaced the static `grade_docs → generate` edge with a conditional edge via `_route_after_grade()`: if `graded_chunks` is empty AND `rewrite_count < MAX_REWRITES (2)`, routes to `rewrite_query → retrieve`; otherwise routes to `generate`. `generate` handles the empty-chunks fallback gracefully (existing behaviour preserved).
- `dependencies.py` — `get_compiled_graph()` now passes `embedding_provider` to `build_graph()`.
- `api/chat.py` — Fully implemented `POST /api/chat/query`: (1) resolve or create `ChatSession` in Postgres, (2) resolve `document_ids` (if empty, fetch all complete document IDs from DB), (3) guard for zero documents, (4) build `AgentState` and `await graph.ainvoke()`, (5) persist user + assistant `Message` rows, (6) return `QueryResponse`.

### Frontend

- `api/client.ts` — Typed Axios wrapper: `uploadDocument`, `listDocuments`, `deleteDocument`, `queryDocuments`.
- `components/SourceCard.tsx` — Displays a single cited chunk (document name + page + content excerpt). Does not parse inline `[file, p.N]` strings — source metadata is already structured in the API response.
- `components/DocumentList.tsx` — Checkbox list of documents with status colour-coding and delete. Only `complete` documents are selectable.
- `components/ChatWindow.tsx` — Auto-scrolling message thread; renders `SourceCard` list under assistant messages.
- `pages/Upload.tsx` — File picker + upload button + status feedback.
- `pages/Chat.tsx` — Two-panel layout: document selector sidebar (polls every 4s for status) + chat area with Enter-to-send textarea. Maintains `sessionId` across turns for conversation continuity.
- `App.tsx` — Top-nav tabs between Chat and Upload pages (no router dependency needed).

**Key decisions:**
- `embedding_provider` is now a required arg to `build_graph()` — the `retrieve` node needs it but `graph.py` previously only injected `chat_provider` and `vector_store`.
- `document_ids=[]` in the query request means "search all complete documents" — resolved in `chat.py` by querying Postgres for all `status=complete` document IDs before graph invocation. The graph itself always receives a concrete list.
- Frontend source display uses structured `Source` objects from the API rather than regex-parsing inline `[filename, p.N]` strings. The inline citation format in the LLM answer text is still present for readability but the source cards are driven by the `sources` array in the response.
- `MAX_REWRITES = 2` defined as a module-level constant in `graph.py` — easy to tune without touching routing logic.

**Verification path:**
1. `docker compose up`
2. Upload a PDF via the Upload tab (or `POST /api/documents/upload`)
3. Wait for status to become `complete` (Chat sidebar polls every 4s)
4. Ask a question in the Chat tab — confirm answer + source cards appear
5. Ask a deliberately off-topic question — check logs for `rewrite_query` node firing (`rewrite_count=1`)
6. Check `GET /api/chat/query` response shape matches `QueryResponse` schema
