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
- [ ] `services/ingestion.py` → `parse_document()`: pypdf + python-docx + plain text
- [ ] `services/ingestion.py` → `chunk_pages()`: RecursiveCharacterTextSplitter with tiktoken
- [ ] `services/vector_store.py` → `query()`: per-collection query, merge + sort by distance
- [ ] `api/documents.py` → `upload_document()`: save temp file, create DB record, background ingest
- [ ] `api/documents.py` → `list_documents()`, `delete_document()`
- [ ] Run `alembic init` and generate first migration from models

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
- Alembic async setup — use `alembic-utils` or standard async engine pattern?
- ChromaDB async client availability — verify `chromadb.AsyncHttpClient` is stable in 0.5.15
- Citation parsing in SourceCard.tsx — regex on `[filename, p.N]` pattern or structured response?
