# DocuSense

An agentic RAG (Retrieval-Augmented Generation) system for document Q&A.
Upload PDFs, DOCX, or text files — ask questions and get grounded answers with source citations.

## Architecture

- **LangGraph agent**: multi-node pipeline (retrieve → grade_docs → generate)
- **LLM**: provider-agnostic — Claude (default), Azure OpenAI, or OpenAI, swapped via config
- **Embeddings**: Azure OpenAI or OpenAI (Claude has no embeddings API)
- **Vector store**: ChromaDB (self-hosted, persistent)
- **Metadata**: PostgreSQL via SQLAlchemy async
- **API**: FastAPI
- **Frontend**: React + TypeScript

For architectural decisions and rationale, see [CLAUDE.md](./CLAUDE.md).
For current development state, see [AGENT_NOTES.md](./AGENT_NOTES.md).

## Quick Start

```bash
cp .env.example .env
# Add your ANTHROPIC_API_KEY and OPENAI_API_KEY (for embeddings) to .env

docker-compose up
# Backend:  http://localhost:8080
# Frontend: http://localhost:3000
# ChromaDB: http://localhost:8000
```

## Local Dev (without Docker)

```bash
# Start Postgres + ChromaDB via Docker, run backend locally
docker-compose up postgres chromadb -d

cd backend
pip install -r ../requirements.txt
uvicorn backend.main:app --reload --port 8080
```

## Provider Configuration

| Use case | LLM_PROVIDER | EMBEDDING_PROVIDER | Keys needed |
|---|---|---|---|
| Claude (default) | `claude` | `openai` | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |
| Azure only | `azure_openai` | `azure_openai` | Azure credentials |
| OpenAI only | `openai` | `openai` | `OPENAI_API_KEY` |
| No API keys (dev) | any | any | none (`USE_MOCK_LLM=true`) |

## Project Structure

```
backend/
  agent/          # LangGraph graph, nodes, state, prompts
  api/            # FastAPI route handlers
  services/       # llm_provider, vector_store, ingestion
  models/         # SQLAlchemy ORM models
  db/             # engine, base, migrations
frontend/
  src/pages/      # Upload, Chat
  src/components/ # ChatWindow, DocumentList, SourceCard
```
