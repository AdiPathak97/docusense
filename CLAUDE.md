# CLAUDE.md — DocuSense: Agentic RAG Document Q&A System

> **Single source of truth for any agent or developer working on this codebase.**
> Load this file at the start of every session. Do not summarise or strip it during context compaction.
> Update deliberately when architecture changes — not during routine feature work.

---

## 1. What This Project Is

DocuSense is a RAG system with an agentic retrieval pipeline. Users upload documents (PDF, DOCX, TXT),
which are chunked, embedded, and stored in a vector store. A LangGraph agent answers questions over
those documents using semantic search + LLM synthesis, with inline source citations.

**Built to demonstrate:**
- Production-grade RAG pipeline design
- Agentic orchestration via LangGraph (not a simple chain)
- Provider-agnostic LLM integration: Claude (primary), Azure OpenAI, OpenAI
- FastAPI backend design patterns
- Context engineering awareness (this document is evidence of that)

This is **not** a simple embed → retrieve → generate chain. It is a multi-node LangGraph agent
where retrieval, grading, and generation are separate, inspectable nodes. This was deliberate —
see §3.1 for why.

---

## 2. Repository Layout

```
docusense/
├── CLAUDE.md                  ← You are here. Load this first, always.
├── AGENT_NOTES.md             ← Session scratchpad. Read before acting.
├── README.md                  ← Setup guide and provider config table
│
├── backend/
│   ├── main.py                ← FastAPI app, router registration, startup hook
│   ├── config.py              ← All env vars via pydantic-settings. No os.getenv() elsewhere.
│   ├── dependencies.py        ← FastAPI DI: singletons created once, injected via Depends()
│   │
│   ├── api/
│   │   ├── documents.py       ← Upload, list, delete document endpoints
│   │   └── chat.py            ← Query endpoint, session management
│   │
│   ├── agent/
│   │   ├── graph.py           ← LangGraph StateGraph definition
│   │   ├── nodes.py           ← Node functions: retrieve, grade_docs, generate
│   │   ├── state.py           ← AgentState TypedDict — shared state schema
│   │   └── prompts.py         ← All LLM prompts. Never write prompts inline elsewhere.
│   │
│   ├── services/
│   │   ├── llm_provider.py    ← Provider abstraction (Claude, AzureOpenAI, OpenAI, Mock)
│   │   ├── vector_store.py    ← ChromaDB client wrapper
│   │   └── ingestion.py       ← Parse → chunk → embed → upsert pipeline
│   │
│   ├── models/
│   │   ├── document.py        ← SQLAlchemy: Document, Chunk
│   │   └── session.py         ← SQLAlchemy: ChatSession, Message
│   │
│   └── db/
│       ├── base.py            ← DeclarativeBase, async engine, get_db()
│       └── migrations/        ← Alembic scripts
│
├── frontend/
│   └── src/
│       ├── pages/             ← Upload.tsx, Chat.tsx
│       ├── components/        ← ChatWindow, DocumentList, SourceCard
│       └── api/client.ts      ← Typed Axios client
│
├── docker-compose.yml         ← backend + frontend + postgres + chromadb
├── Dockerfile.backend
├── requirements.txt
└── .env.example
```

---

## 3. Architecture: Why It Was Built This Way

### 3.1 LangGraph over a simple chain

A naive RAG implementation would be: query → embed → similarity_search → stuff_into_prompt → generate.
Rejected for two reasons:

1. **Observability**: In a chain, if the answer is wrong, you cannot tell whether retrieval or generation
   failed. Separate graph nodes are independently logged and inspectable.
2. **Grading node**: `grade_docs` filters retrieved chunks that are semantically close but contextually
   irrelevant to the specific question. This reduces hallucination and is awkward to implement cleanly
   in a chain.

Graph topology (v1): `retrieve → grade_docs → generate`
Planned (v2): `grade_docs → rewrite_query → retrieve` when all chunks are filtered out.

### 3.2 ChromaDB over FAISS

- Runs as a persistent server (not in-memory) — suitable for a multi-request API
- REST interface — swappable as a Docker sidecar
- FAISS requires index file serialisation — complexity with no benefit at this scale

Do not switch to FAISS without a performance benchmark that justifies it.

### 3.3 Provider-agnostic LLM layer (Claude primary)

**Claude is the primary chat provider.** This is intentional and not accidental:
- The JD this project was built for explicitly requires Claude experience
- The `ClaudeProvider` in `services/llm_provider.py` uses the `anthropic` Python SDK directly

**Important**: Claude has no embeddings API. Chat and embedding are therefore separate protocols
(`LLMChatProvider`, `EmbeddingProvider`). `LLM_PROVIDER` and `EMBEDDING_PROVIDER` are configured
independently. When `LLM_PROVIDER=claude`, embeddings fall back to `EMBEDDING_PROVIDER`
(default: `openai`).

The provider is injected into LangGraph nodes via `functools.partial` in `graph.py` — nodes
call `provider.complete(system, user)` and are unaware of which provider is active.

Azure OpenAI and OpenAI are also implemented for portability. Switch via `LLM_PROVIDER` in `.env`.

### 3.4 PostgreSQL for metadata, not ChromaDB

ChromaDB stores: vectors + chunk text + minimal metadata.
PostgreSQL stores: document records, chunk index/page metadata, chat sessions, message history.

Relational queries ("all chunks for document X", "messages in session Y") are better expressed
in SQL than ChromaDB's metadata filter syntax.

### 3.5 No streaming in v1

Streaming deferred because:
- Complicates the agent graph (nodes must yield tokens, not return strings)
- Portfolio goal is correctness and architecture, not UX polish

To add streaming: replace `JSONResponse` with `StreamingResponse` in `chat.py`,
update LangGraph invocation to use `.astream()`.

---

## 4. Data Flow

```
[Upload]
POST /api/documents/upload
  → ingestion.py: parse → chunk → embed → upsert to ChromaDB
  → DB: Document + Chunk rows inserted

[Query]
POST /api/chat/query
  → LangGraph agent:
      retrieve    → embed question, query ChromaDB top-k
      grade_docs  → LLM scores each chunk yes/no (GRADE prompt)
      generate    → LLM synthesises answer with citations (GENERATE prompt)
  → DB: Message rows persisted (user + assistant)
  → Response: { answer, session_id, sources }
```

---

## 5. Environment Variables

All vars are in `config.py` via pydantic-settings. Never use `os.getenv()` elsewhere.
Canonical reference: `.env.example`.

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `claude` / `azure_openai` / `openai` |
| `ANTHROPIC_API_KEY` | Required when `LLM_PROVIDER=claude` |
| `EMBEDDING_PROVIDER` | `azure_openai` / `openai` (Claude has no embeddings API) |
| `AZURE_OPENAI_*` | Required when provider is `azure_openai` |
| `OPENAI_API_KEY` | Required when provider is `openai` or embedding is `openai` |
| `DATABASE_URL` | PostgreSQL async connection string |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB server |
| `TOP_K_RETRIEVAL` | Chunks to retrieve per query (default: 5) |
| `RELEVANCE_THRESHOLD` | Min grade score to keep chunk (default: 0.6) |
| `USE_MOCK_LLM` | Bypass all API calls with canned responses (dev only) |

---

## 6. Constraints — Do Not Reverse Without Updating This File

1. **All prompts in `agent/prompts.py`.** Never write prompt strings inline in nodes or services.
2. **AgentState is the only shared state during a graph run.** No DB writes or Redis writes
   mid-graph. Side effects happen after `graph.ainvoke()` returns.
3. **ChromaDB collections namespaced by document ID** (`doc_{uuid}`). Multi-tenancy is the
   API layer's responsibility — filter by `document_ids` passed to the query.
4. **Chunk size: 500 tokens, overlap: 50.** Changing this requires re-embedding all documents.
   Increment `EMBEDDING_VERSION` in `ingestion.py` and add a migration script.
5. **Frontend is intentionally minimal.** Do not invest in frontend polish unless explicitly asked.
6. **Citation format `[filename, p.N]`** is parsed by `SourceCard.tsx`. Do not change the format
   in `GENERATE_USER` prompt without updating the frontend component.

---

## 7. Out of Scope (v1)

- Authentication / user accounts
- Streaming responses
- Multi-document cross-query (each query targets one or more explicit document collections)
- Query rewriting on low-relevance retrieval (planned v2 node)
- LLM evaluation framework (ragas / ARES)
- Production deployment hardening

---

## 8. Context Engineering Notes (Meta)

This document is an exercise in the principles described in:
[Effective context engineering for AI agents — Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

- **Stable vs. dynamic context**: this file (stable architectural facts) is separate from
  `AGENT_NOTES.md` (evolving session state) — mirroring the hybrid retrieval model.
- **Constraint visibility**: §6 exists to prevent an agent from making locally reasonable
  decisions that contradict system design, because the reasoning is now visible.
- **No assumed shared context**: every decision records its rationale so a new agent or
  developer does not need to reverse-engineer intent from code.

---

*Update this file when: adding a new service, changing graph topology, altering chunking
strategy, modifying the DB schema, or adding a new LLM provider.*
