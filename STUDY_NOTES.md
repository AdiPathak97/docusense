# DocuSense — Study Notes

> Concepts learned while building this project, connected to the actual code.
> Updated as we implement each phase. Use this to revise — find the concept, then open the file.

---

## Table of Contents

1. [Python Backend Fundamentals](#1-python-backend-fundamentals)
   - [1.1 Configuration Management — pydantic-settings](#11-configuration-management--pydantic-settings)
   - [1.2 Python Module as Singleton](#12-python-module-as-singleton)
   - [1.3 Structural Typing — Protocol](#13-structural-typing--protocol)
   - [1.4 Lazy Imports for Optional Dependencies](#14-lazy-imports-for-optional-dependencies)
   - [1.5 The Factory Function Pattern](#15-the-factory-function-pattern)
   - [1.6 Enums that Serialise to Strings](#16-enums-that-serialise-to-strings)
   - [1.7 TypedDict — Typed Dictionaries](#17-typeddict--typed-dictionaries)
   - [1.8 functools.partial — Pre-filling Function Arguments](#18-functoolspartial--pre-filling-function-arguments)
2. [Async Python](#2-async-python)
   - [2.1 async/await and the Event Loop](#21-asyncawait-and-the-event-loop)
   - [2.2 asyncio.gather — Parallel Coroutines](#22-asynciogather--parallel-coroutines)
   - [2.3 Async Factory Functions — Awaitable Constructors](#23-async-factory-functions--awaitable-constructors)
3. [FastAPI Patterns](#3-fastapi-patterns)
   - [3.1 Dependency Injection with Depends()](#31-dependency-injection-with-depends)
   - [3.2 lru_cache as a Singleton](#32-lru_cache-as-a-singleton)
   - [3.3 Generator Dependencies — yield in get_db()](#33-generator-dependencies--yield-in-get_db)
   - [3.4 BackgroundTasks — Non-blocking Deferred Work](#34-backgroundtasks--non-blocking-deferred-work)
   - [3.5 Structured Error Logging — Never Swallow Exceptions Silently](#35-structured-error-logging--never-swallow-exceptions-silently)
   - [3.6 Global Exception Handlers — Centralised HTTP Error Responses](#36-global-exception-handlers--centralised-http-error-responses)
   - [3.7 Request-Scoped Context — ContextVar + logging.Filter](#37-request-scoped-context--contextvar--loggingfilter)
   - [3.8 db.flush() vs db.commit() — Getting Generated IDs Mid-Transaction](#38-dbflush-vs-dbcommit--getting-generated-ids-mid-transaction)
4. [SQLAlchemy ORM (v2)](#4-sqlalchemy-orm-v2)
   - [4.1 Mapped Annotations — Typed Columns](#41-mapped-annotations--typed-columns)
   - [4.2 Async Engine and asyncpg](#42-async-engine-and-asyncpg)
   - [4.3 Relationships and Cascade Delete](#43-relationships-and-cascade-delete)
   - [4.4 Default Values — Why Use a Lambda](#44-default-values--why-use-a-lambda)
   - [4.5 Background Task Session Isolation](#45-background-task-session-isolation)
5. [Logging & Observability](#5-logging--observability)
   - [5.1 Python Logging Architecture — The Hierarchy](#51-python-logging-architecture--the-hierarchy)
   - [5.2 dictConfig — Configuring Logging Declaratively](#52-dictconfig--configuring-logging-declaratively)
   - [5.3 warnings vs logging — Two Separate Systems](#53-warnings-vs-logging--two-separate-systems)
   - [5.4 exception() vs error() — When to Print a Traceback](#54-exception-vs-error--when-to-print-a-traceback)
   - [5.5 Custom Exception Hierarchies](#55-custom-exception-hierarchies)
6. [AI Engineering Concepts](#6-ai-engineering-concepts)
   - [5.1 RAG — Retrieval-Augmented Generation](#51-rag--retrieval-augmented-generation)
   - [5.2 Embeddings and Vector Search](#52-embeddings-and-vector-search)
   - [5.3 Chunking Strategy](#53-chunking-strategy)
   - [5.4 LangGraph — Agent Graph vs. Chain](#54-langgraph--agent-graph-vs-chain)
   - [5.5 Prompt Engineering as Code](#55-prompt-engineering-as-code)
   - [5.6 Provider Abstraction — Swappable LLMs](#56-provider-abstraction--swappable-llms)
   - [5.7 PDF Text Extraction — Why Library Choice Matters](#57-pdf-text-extraction--why-library-choice-matters)
   - [5.8 LangGraph Conditional Edges — Routing Between Nodes at Runtime](#58-langgraph-conditional-edges--routing-between-nodes-at-runtime)
   - [5.9 Agentic Loop Pattern — Query Rewriting with a Max-Retry Cap](#59-agentic-loop-pattern--query-rewriting-with-a-max-retry-cap)
7. [Software Engineering Principles & Design Patterns](#7-software-engineering-principles--design-patterns)
   - [7.1 Fail Fast vs Graceful Degradation](#71-fail-fast-vs-graceful-degradation)
   - [7.2 Defense in Depth — Layered Error Handling](#72-defense-in-depth--layered-error-handling)
   - [7.3 Chain of Responsibility Pattern](#73-chain-of-responsibility-pattern)
   - [7.4 Separation of Concerns](#74-separation-of-concerns)
   - [7.5 The 12-Factor App Methodology](#75-the-12-factor-app-methodology)
   - [7.6 Observability in System Design](#76-observability-in-system-design)
   - [7.7 Open/Closed Principle Applied to Error Hierarchies](#77-openclosed-principle-applied-to-error-hierarchies)
   - [7.8 Correlation IDs — Tracing Requests Across Layers](#78-correlation-ids--tracing-requests-across-layers)
8. [Frontend Development — React + Vite + TypeScript](#8-frontend-development--react--vite--typescript)
   - [8.1 Vite Dev Server + Docker — The Host Binding Problem](#81-vite-dev-server--docker--the-host-binding-problem)
   - [8.2 Typed Axios Client Pattern](#82-typed-axios-client-pattern)
   - [8.3 React Hooks for Async State](#83-react-hooks-for-async-state)
   - [8.4 Polling with setInterval for Live Status Updates](#84-polling-with-setinterval-for-live-status-updates)
   - [8.5 FormData for File Uploads](#85-formdata-for-file-uploads)
9. [Changelog](#9-changelog)

---

## 1. Python Backend Fundamentals

---

### 1.1 Configuration Management — pydantic-settings

**Concept:** Instead of scattering `os.getenv()` calls throughout code, centralise all environment
variable access in one validated class. The app fails at startup if config is wrong — not silently
at runtime during a request.

**Reference:** [backend/config.py](backend/config.py)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["claude", "azure_openai", "openai"] = "claude"
    chroma_port: int = 8000          # pydantic casts "8000" string → int automatically
    use_mock_llm: bool = False
```

**Key points:**
- `BaseSettings` reads from `.env` file and real environment variables — env vars win over `.env`
- Fields have types: `int`, `bool`, `str`, `Literal[...]` — pydantic validates and casts on load
- `Literal["claude", "azure_openai", "openai"]` means the field can only hold one of those values.
  Setting `LLM_PROVIDER=typo` in `.env` raises a `ValidationError` at startup.
- `extra="ignore"` — unknown env vars are silently ignored (useful in CI with many injected vars)
- `CLAUDE.md §5` and `CLAUDE.md §6` reinforce: **never use `os.getenv()` elsewhere in the codebase**

**Compare:**
```python
# ❌ Naive — scattered, untyped, silent failures
api_key = os.getenv("ANTHROPIC_API_KEY")  # could be None, you won't know until it crashes
port = int(os.getenv("PORT", "8000"))     # manual casting, duplicated everywhere

# ✅ pydantic-settings — one place, validated, typed
settings.anthropic_api_key   # always str
settings.chroma_port         # always int
```

---

### 1.2 Python Module as Singleton

**Concept:** Python imports a module only once per interpreter session. A module-level variable is
therefore a singleton — every file that imports it gets the same object.

**Reference:** [backend/config.py](backend/config.py) (last line), [backend/dependencies.py](backend/dependencies.py)

```python
# config.py — bottom of file
settings = Settings()   # constructed once when module is first imported

# anywhere else in the codebase
from backend.config import settings   # same object, no re-construction
```

**Why this works:** Python's import system caches modules in `sys.modules`. The second `import`
of the same module returns the cached module — it does not re-execute the file. So `settings = Settings()`
runs exactly once.

**When to use:** Stateless or read-only objects (config, constants). For stateful singletons
(DB connections, compiled graphs), use `@lru_cache` on a factory function (see §3.2).

---

### 1.3 Structural Typing — Protocol

**Concept:** Python's `Protocol` defines a "shape" a class must match — without requiring inheritance.
If a class has the right methods with the right signatures, it satisfies the Protocol. This is
called **structural subtyping** (or formalised duck typing).

**Reference:** [backend/services/llm_provider.py](backend/services/llm_provider.py) — lines 18–28

```python
@runtime_checkable
class LLMChatProvider(Protocol):
    async def complete(self, system: str, user: str) -> str: ...

# ClaudeProvider satisfies LLMChatProvider — WITHOUT inheriting from it
class ClaudeProvider:
    async def complete(self, system: str, user: str) -> str:
        ...   # real implementation
```

**Protocol vs ABC:**

| | `Protocol` | `ABC` (Abstract Base Class) |
|---|---|---|
| Inheritance required? | ❌ No | ✅ Yes |
| Type checker enforces it? | ✅ Yes | ✅ Yes |
| `isinstance()` check at runtime? | Only with `@runtime_checkable` | ✅ Always |
| Best for? | Classes you don't control, or unrelated classes that share a shape | Your own class hierarchy |

**Why Protocol here:** `ClaudeProvider`, `OpenAIChatProvider`, and `MockChatProvider` are completely
unrelated classes that happen to share the same method signature. Forcing them to inherit from a
common base would be artificial. Protocol lets type checkers verify the contract without coupling
the classes together.

**`@runtime_checkable`** enables `isinstance(provider, LLMChatProvider)` — useful for assertions
in tests: `assert isinstance(provider, LLMChatProvider)`.

---

### 1.4 Lazy Imports for Optional Dependencies

**Concept:** Import a library inside `__init__` (or any method) instead of at the top of the file.
The import only runs when that class is actually instantiated, not when the module is loaded.

**Reference:** [backend/services/llm_provider.py](backend/services/llm_provider.py) — lines 37–38

```python
class ClaudeProvider:
    def __init__(self, settings: Settings):
        import anthropic          # ← inside __init__, not at top of file
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
```

**Why:** If `import anthropic` were at the top of `llm_provider.py`, then anyone importing that
file — even to use `OpenAIChatProvider` — would require the `anthropic` package to be installed.
By deferring it, `anthropic` is only needed when `LLM_PROVIDER=claude` and `ClaudeProvider` is
actually constructed. Running with `LLM_PROVIDER=openai` never touches that import.

**Trade-off:** Slightly unconventional; tools that scan top-level imports (like some linters) may
miss it. Acceptable for optional, heavy dependencies.

---

### 1.5 The Factory Function Pattern

**Concept:** A function that decides which concrete class to build, based on runtime conditions.
Callers receive an interface type, not a concrete type — they don't know which implementation
they got.

**Reference:** [backend/services/llm_provider.py](backend/services/llm_provider.py) — lines 146–165

```python
def get_chat_provider(settings: Settings) -> LLMChatProvider:
    if settings.use_mock_llm:
        return MockChatProvider()
    if settings.llm_provider == "claude":
        return ClaudeProvider(settings)
    if settings.llm_provider == "azure_openai":
        return AzureOpenAIChatProvider(settings)
    if settings.llm_provider == "openai":
        return OpenAIChatProvider(settings)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")   # guard clause
```

**Key points:**
- The caller gets `LLMChatProvider` (the Protocol type) — they call `.complete()` and don't care
  which provider is underneath. This is the **Dependency Inversion Principle**.
- `raise ValueError` at the end is a **guard clause** — if someone adds a new `Literal` value
  to `llm_provider` in config but forgets to add a branch here, they get a clear error
  immediately rather than a `None` silently propagating.
- `use_mock_llm` check comes first — it takes priority over the provider setting. This lets you
  override any provider with the mock during development.

---

### 1.6 Enums that Serialise to Strings

**Concept:** Inheriting both `str` and `enum.Enum` makes each member also a plain string.
This means it serialises to JSON naturally and compares equal to its string value.

**Reference:** [backend/models/document.py](backend/models/document.py) — lines 9–13

```python
class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"
```

**Why inherit `str`:**
```python
# Plain enum.Enum
class Status(enum.Enum):
    pending = "pending"

json.dumps(Status.pending)          # ❌ TypeError — not serialisable
Status.pending == "pending"         # ❌ False

# str + enum.Enum
class ProcessingStatus(str, enum.Enum):
    pending = "pending"

json.dumps(ProcessingStatus.pending)    # ✅ "pending"
ProcessingStatus.pending == "pending"   # ✅ True
```

**Use this pattern** whenever an enum needs to live in a DB column (SQLAlchemy stores it as a
string), be returned in an API response, or be compared to raw strings from external sources.

---

### 1.7 TypedDict — Typed Dictionaries

**Concept:** `TypedDict` is a plain `dict` at runtime, but statically typed. Type checkers know
what keys exist and what types they hold — you get autocomplete and typo detection.

**Reference:** [backend/agent/state.py](backend/agent/state.py)

```python
class DocumentChunk(TypedDict):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    relevance_score: float | None

class AgentState(TypedDict):
    question: str
    retrieved_chunks: list[DocumentChunk]
    graded_chunks: list[DocumentChunk]
    answer: str
    sources: list[DocumentChunk]
```

**Why TypedDict instead of a dataclass or Pydantic model?**
LangGraph's state must be a dict — nodes receive a dict and return a partial dict that LangGraph
merges into the shared state. If you used a dataclass, LangGraph couldn't merge partial updates.
`TypedDict` gives you type safety while staying a dict under the hood.

```python
# Nodes return only the keys they populate — other keys are untouched by LangGraph
async def grade_docs(state: AgentState, ...) -> dict:
    return {"graded_chunks": graded}   # only this key is updated in the shared state
```

**`float | None`** (Python 3.10+ union syntax) means `relevance_score` can be a float or `None`.
Equivalent to `Optional[float]` in older Python.

---

### 1.8 functools.partial — Pre-filling Function Arguments

**Concept:** `functools.partial` creates a new callable with some arguments pre-filled. The
resulting function has a shorter signature — only the remaining arguments need to be passed.

**Reference:** [backend/agent/graph.py](backend/agent/graph.py) — lines 25–27

```python
import functools

graph.add_node("retrieve",   functools.partial(retrieve,   vector_store=vector_store))
graph.add_node("grade_docs", functools.partial(grade_docs, chat_provider=chat_provider))
```

**Why:** LangGraph calls node functions as `node(state)` — one argument only. But `retrieve`
is defined as `async def retrieve(state, vector_store)`. `partial` bridges this gap:

```python
# retrieve needs 2 args
async def retrieve(state: AgentState, vector_store: VectorStoreClient) -> dict: ...

# partial pre-fills vector_store, returning a function that only needs state
bound = functools.partial(retrieve, vector_store=vs)
await bound(state)   # LangGraph can call this — it only passes state
```

**Benefit:** The node functions stay pure and testable — in tests you can call
`retrieve(state, vector_store=mock_store)` directly without needing the graph. `partial` is
the glue between "how LangGraph calls nodes" and "what dependencies nodes need".

---

## 2. Async Python

---

### 2.1 async/await and the Event Loop

**Concept:** `async def` declares a coroutine — a function that can pause at `await` points and
let the event loop run other work while waiting for I/O (network call, DB query, file read).
This allows a single-threaded Python process to handle many concurrent requests.

**Reference:** [backend/agent/nodes.py](backend/agent/nodes.py) (all node functions), [backend/services/llm_provider.py](backend/services/llm_provider.py)

```python
async def grade_docs(state: AgentState, chat_provider: LLMChatProvider) -> dict:
    graded = []
    for chunk in state["retrieved_chunks"]:
        response = await chat_provider.complete(...)  # suspends here — event loop runs other work
        if response.strip().lower() == "yes":
            graded.append(chunk)
    return {"graded_chunks": graded}
```

**What happens at `await`:**
1. `grade_docs` suspends — gives control back to the event loop
2. Event loop processes other requests, timers, completed I/O
3. When the API response arrives, event loop resumes `grade_docs` from that line

**Contrast with threads:** Threads run truly in parallel (on multiple CPU cores) but share memory
unsafely. Async is single-threaded — only one coroutine runs at a time, but the event loop
switches between them at `await` points. For I/O-bound work (network calls, DB), async is
as fast as threads and far simpler.

**Rule:** `async def` functions must be `await`ed. Regular functions cannot `await` coroutines.
If you call an `async def` without `await`, you get a coroutine object — not the result.

---

### 2.2 asyncio.gather — Parallel Coroutines

**Concept:** `asyncio.gather(*coroutines)` runs multiple coroutines concurrently and waits for
all of them to finish. It's the async equivalent of running tasks in parallel.

**Reference:** [backend/agent/nodes.py](backend/agent/nodes.py) — mentioned in comment on `grade_docs`, not yet implemented

```python
# Current implementation — serial (one API call at a time)
for chunk in state["retrieved_chunks"]:
    response = await chat_provider.complete(...)   # waits for each before moving on

# Better implementation — parallel (all API calls at once)
import asyncio

tasks = [
    chat_provider.complete(GRADE_SYSTEM, GRADE_USER.format(question=..., chunk_content=chunk["content"]))
    for chunk in state["retrieved_chunks"]
]
responses = await asyncio.gather(*tasks)   # all 5 LLM calls fire simultaneously

graded = [
    chunk for chunk, r in zip(state["retrieved_chunks"], responses)
    if r.strip().lower() == "yes"
]
```

**Trade-off:**
- Serial: easier to reason about, easier to debug, errors are isolated
- Parallel: proportionally faster (5 chunks → ~1x latency instead of ~5x), but one failure
  in `gather` raises an exception for all tasks by default

**When to use `gather`:** Whenever you have independent I/O calls — each chunk grading is
independent of the others. Don't use it when call B depends on the result of call A.

---

### 2.3 Async Factory Functions — Awaitable Constructors

**Concept:** Some libraries expose an async factory function instead of a regular constructor.
Calling it returns a coroutine — you must `await` it to get the actual object. Forgetting the
`await` gives you a coroutine object, not the client, so the first method call on it fails.

**Reference:** [backend/services/vector_store.py](backend/services/vector_store.py) — `_get_client()`

```python
# ❌ Wrong — chromadb.AsyncHttpClient() returns a coroutine, not a client
self._client = chromadb.AsyncHttpClient(host=..., port=...)
self._client.get_or_create_collection(...)  # AttributeError: 'coroutine' has no attribute ...

# ✅ Correct — await the factory call
self._client = await chromadb.AsyncHttpClient(host=..., port=...)
```

**Problem:** `__init__` cannot be `async def`. So you can't `await` inside a constructor.

**Solution — lazy initialisation:**
```python
class VectorStoreClient:
    def __init__(self):
        self._client = None   # not yet created

    async def _get_client(self):
        if self._client is None:
            self._client = await chromadb.AsyncHttpClient(host=..., port=...)
        return self._client

    async def upsert_chunks(self, ...):
        client = await self._get_client()   # initialises on first call, reuses after
        collection = await client.get_or_create_collection(...)
```

**Why it's safe here:** `VectorStoreClient` is a `@lru_cache` singleton. Only one instance
exists for the process lifetime. The first async call initialises `_client`; all subsequent
calls reuse it. There is no true concurrency risk in a single-worker asyncio app.

**Recognising the pattern:** If a library's docs show `client = await SomeClient(...)` — that's
an async factory. Common in async HTTP libraries, async DB drivers, and async message brokers.

---

## 3. FastAPI Patterns

---

### 3.1 Dependency Injection with Depends()

**Concept:** FastAPI's `Depends()` is a built-in dependency injection system. You declare what
a route needs as a parameter, FastAPI resolves and provides it. Dependencies can depend on
other dependencies — FastAPI builds a resolution graph.

**Reference:** [backend/api/documents.py](backend/api/documents.py), [backend/api/chat.py](backend/api/chat.py), [backend/dependencies.py](backend/dependencies.py)

```python
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),                        # ← DI: get a DB session
    vector_store = Depends(get_vector_store),                  # ← DI: get the VectorStoreClient
    embedding_provider = Depends(get_embedding_provider_dep),  # ← DI: get embedding provider
):
    ...
```

**Why this is better than global variables:**
- **Testability:** In tests, override a dependency to inject a mock:
  `app.dependency_overrides[get_vector_store] = lambda: MockVectorStore()`
- **Separation of concerns:** Route handlers describe *what they need*, not *how to get it*
- **Lifecycle management:** `yield`-based dependencies (like `get_db`) get cleanup code that
  runs after the request, even on error

**FastAPI resolves the graph:** If `get_compiled_graph` depends on `get_chat_provider_dep` and
`get_vector_store`, FastAPI (and `lru_cache`) ensures these are resolved once and reused.

---

### 3.2 lru_cache as a Singleton

**Concept:** `@lru_cache` caches the return value of a function. For functions with no arguments,
this means the function body runs exactly once — every subsequent call returns the cached result.
This is the standard Python idiom for singletons.

**Reference:** [backend/dependencies.py](backend/dependencies.py)

```python
from functools import lru_cache

@lru_cache
def get_vector_store() -> VectorStoreClient:
    return VectorStoreClient()   # runs once; all calls return the same object

@lru_cache
def get_compiled_graph():
    return build_graph(          # LangGraph compilation is expensive — do it once
        chat_provider=get_chat_provider_dep(),
        vector_store=get_vector_store(),
    )
```

**Why FastAPI's `Depends()` alone isn't enough:** `Depends(get_vector_store)` calls
`get_vector_store()` on every request. Without `@lru_cache`, that would create a new
`VectorStoreClient` (and a new ChromaDB connection) per request. `@lru_cache` ensures
the same instance is returned regardless of how many times the function is called.

**`lru_cache` with arguments:** If a function takes arguments, `lru_cache` caches one result
per unique set of arguments. For zero-argument singletons, there's only ever one cache entry.

---

### 3.3 Generator Dependencies — yield in get_db()

**Concept:** A dependency function that uses `yield` instead of `return` becomes a
context-manager-style dependency. Code before `yield` runs before the request; code after
`yield` (in a `finally` block or `async with` exit) runs after the request, even on error.

**Reference:** [backend/db/base.py](backend/db/base.py) — lines 14–16

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session      # ← FastAPI injects whatever is yielded into the route handler
                           # ← After the handler returns (or raises), execution continues here
                           # ← async with exits: session is committed/rolled back and closed
```

**Execution order:**
```
Request arrives
  → get_db() starts, session created
  → yield session   → route handler receives it
  → route handler runs
  → route handler returns (or raises)
  → get_db() resumes after yield
  → async with block exits → session closed
Response sent
```

**Why this matters:** You never need `try/finally` or explicit `session.close()` in route
handlers. The session is always cleaned up, even if the handler raises an exception. This is
the same pattern as Python's `with` statement — just threaded through FastAPI's DI system.

---

### 3.4 BackgroundTasks — Non-blocking Deferred Work

**Concept:** FastAPI's `BackgroundTasks` lets you schedule a function to run *after* the HTTP
response is sent. The client doesn't wait for the background work to finish.

**Reference:** [backend/api/documents.py](backend/api/documents.py) — `upload_document()`

```python
@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,   # ← FastAPI injects this automatically
    file: UploadFile = File(...),
    ...
):
    # 1. Save file, create DB record — fast
    # 2. Schedule ingestion to run after response
    background_tasks.add_task(ingest, document_id, document_name, file_path, ...)

    return {"document_id": doc.id, "status": "processing"}  # returns immediately
    # ingest() runs here, after the response is sent
```

**Why:** Document ingestion (parse → chunk → embed → upsert) takes seconds. Blocking the
HTTP request for that long would:
- Time out on slow connections
- Hold a DB session open unnecessarily
- Block other requests on the same worker (in some server configurations)

**Limitation:** If the server process crashes, the background task is lost. For production
reliability, use a proper task queue (Celery + Redis, or ARQ). For a portfolio app,
`BackgroundTasks` is clean and appropriate.

---

### 3.5 Structured Error Logging — Never Swallow Exceptions Silently

**Concept:** A bare `except Exception: pass` (or setting a status flag without logging) hides
failures completely. Always log before swallowing an exception — in background tasks especially,
uncaught exceptions disappear silently otherwise.

**Reference:** [backend/api/documents.py](backend/api/documents.py) — `_run_ingestion()`

```python
logger = logging.getLogger(__name__)   # module-level logger, named after the file

async def _run_ingestion(...):
    try:
        ...
    except DocuSenseError as exc:
        logger.error("Ingestion failed [%s] — document_id=%s: %s",
                     type(exc).__name__, document_id, exc)
        # clean single-line log; typed message is self-describing
    except Exception:
        logger.exception("Unexpected ingestion error — document_id=%s", document_id)
        # unknown error: log with full traceback
```

**`logging.getLogger(__name__)`:**
- `__name__` is the module's dotted import path (e.g. `backend.api.documents`)
- Logger inherits level/handler config from `backend` without individual setup
- Enables subtree silencing: `logging.getLogger("backend").setLevel(logging.WARNING)`

See §5.4 for the full `exception()` vs `error()` rule.

---

### 3.6 Global Exception Handlers — Centralised HTTP Error Responses

**Concept:** Register handlers on the FastAPI app for exception types. They intercept any
exception that escapes route handlers and convert it to a structured JSON response — one place,
consistent format, no raw stack traces ever reaching the client.

**Reference:** [backend/main.py](backend/main.py) — `docusense_error_handler`, `unhandled_exception_handler`

```python
@app.exception_handler(DocuSenseError)
async def docusense_error_handler(request: Request, exc: DocuSenseError) -> JSONResponse:
    logger.error("DocuSenseError [%s] on %s %s: %s",
                 type(exc).__name__, request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={
        "error": type(exc).__name__,   # e.g. "LLMError"
        "detail": str(exc),            # human-readable, safe — no API keys or internal paths
    })

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "InternalServerError",
        "detail": "An unexpected error occurred. Check server logs for details.",
        # ↑ deliberately hides exception message — raw exceptions may contain internal details
    })
```

**Two handlers for two cases:**
- `DocuSenseError` — typed, expected. Message is safe. Log without traceback. Client sees the error type and description.
- `Exception` — unknown. Message is hidden from client. Full traceback logged server-side.

**Registration order matters in FastAPI:** The most specific handler (subclass) is checked first.
`DocuSenseError` matches before the bare `Exception` catch-all.

---

### 3.7 Request-Scoped Context — ContextVar + logging.Filter

**Concept:** Attach per-request metadata (like a unique ID) to every log line emitted during
that request — across all layers — without passing it as a function argument.

**Reference:** [backend/main.py](backend/main.py) — `_request_id_var`, `_RequestIdFilter`, `request_id_middleware`

```python
# 1. A ContextVar holds the current request's ID.
#    Each async task inherits its own copy at the point it's created.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# 2. A logging.Filter stamps every LogRecord with it.
class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get("")
        return True

# 3. Middleware sets the ContextVar for the duration of each request.
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())
    token = _request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        _request_id_var.reset(token)   # restore previous value (important for test isolation)
    response.headers["X-Request-ID"] = rid
    return response
```

**Why `ContextVar` and not a global variable:**
- A global would be overwritten by concurrent requests — all requests would share the last-set ID
- `ContextVar` is asyncio-safe: each coroutine inherits a *copy* of the context, so concurrent
  requests each see their own `request_id`

**Result:** Every log line from every layer carries the same `request_id`, so you can grep
`grep "req-f4a1b2" docker_logs.txt` to see the full lifecycle of one request across all services.

---

### 3.8 db.flush() vs db.commit() — Getting Generated IDs Mid-Transaction

**Concept:** `flush()` sends pending SQL to the database *within the current transaction* without
committing. The DB executes the INSERT and populates any server-generated or default values
(like auto-increment IDs), which are then readable in Python — but the change is not yet
permanent and can still be rolled back.

**Reference:** [backend/api/chat.py](backend/api/chat.py) — session creation in `query()`

```python
# Without flush — session.id may not yet exist if the DB generates it
session = ChatSession()
db.add(session)
# session.id is already populated here because ChatSession uses a Python-level
# default (lambda: str(uuid.uuid4())) — no flush needed in this case.

# When you DO need flush: server-side defaults (SERIAL, DEFAULT NOW(), etc.)
# The DB generates the value; Python doesn't know it until the INSERT executes.
db.add(some_model)
await db.flush()         # sends INSERT to DB, populates some_model.id
print(some_model.id)     # ✅ now available — without flush this would be None
await db.commit()        # makes it permanent
```

**Python-side vs server-side defaults:**

| Default type | Example | Flush needed? |
|---|---|---|
| Python lambda | `default=lambda: str(uuid.uuid4())` | ❌ — Python sets it before the INSERT |
| Python function | `default=datetime.utcnow` | ❌ — Python sets it before the INSERT |
| Server-side SQL | `DEFAULT gen_random_uuid()`, `SERIAL` | ✅ — DB generates it; flush to read it back |

**DocuSense uses Python-level defaults** for all PKs and timestamps, so `flush()` is used
defensively here rather than strictly required. The key pattern to remember is: if you need
a generated value from the DB before committing, call `flush()` first.

**`commit()` vs `flush()` summary:**

| | `flush()` | `commit()` |
|---|---|---|
| Sends SQL to DB? | ✅ | ✅ |
| Still in transaction? | ✅ (rollback still possible) | ❌ (permanent) |
| Visible to other sessions? | ❌ (not yet) | ✅ |
| Use when? | Need generated value mid-request | Request complete, persist permanently |

---

## 4. SQLAlchemy ORM (v2)

---

### 4.1 Mapped Annotations — Typed Columns

**Concept:** SQLAlchemy 2.0 introduced `Mapped[T]` annotations. Each column is declared as a
typed Python attribute — giving both runtime ORM behaviour and static type information to
type checkers and IDEs.

**Reference:** [backend/models/document.py](backend/models/document.py), [backend/models/session.py](backend/models/session.py)

```python
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

**Before SQLAlchemy 2.0 (old style):**
```python
id = Column(String, primary_key=True)   # id is typed as Any — no IDE help
```

**With `Mapped[T]`:** `doc.name` is known to be `str`, `doc.chunk_count` is `int`. The type
checker will catch `doc.chunk_count + "hello"` as an error.

---

### 4.2 Async Engine and asyncpg

**Concept:** The standard SQLAlchemy engine uses `psycopg2` — a synchronous driver that blocks
the thread while waiting for the DB. The async engine uses `asyncpg` — a non-blocking driver
that works with the event loop.

**Reference:** [backend/db/base.py](backend/db/base.py) — line 10; [backend/config.py](backend/config.py) — the `DATABASE_URL`

```python
# Database URL selects the driver:
# postgresql+asyncpg://user:pass@host/db  ← async driver
# postgresql+psycopg2://user:pass@host/db ← sync driver (don't use in FastAPI)

engine = create_async_engine(settings.database_url, echo=False)
```

**Why async matters in FastAPI:** FastAPI is built on asyncio. If a route handler does
`session.execute(query)` with a sync driver, it blocks the entire event loop — no other
requests can be processed while waiting for the DB response. With `asyncpg`, the event loop
switches to other requests during DB I/O.

**`echo=False`** — when `True`, SQLAlchemy prints every SQL query to stdout. Useful for
debugging; never leave it `True` in production (leaks query structure, too noisy).

---

### 4.3 Relationships and Cascade Delete

**Concept:** SQLAlchemy `relationship()` links two ORM models. `cascade="all, delete"` means
that when the parent is deleted, SQLAlchemy automatically deletes all related children.

**Reference:** [backend/models/document.py](backend/models/document.py) — lines 28–29 and 39

```python
class Document(Base):
    chunks: Mapped[list["Chunk"]] = relationship("Chunk", back_populates="document", cascade="all, delete")

class Chunk(Base):
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
```

**`back_populates`** keeps both sides of the relationship in sync:
```python
doc.chunks      # list of Chunk objects
chunk.document  # the parent Document object
```

**`cascade="all, delete"`** — without this, deleting a `Document` would leave orphaned `Chunk`
rows in the DB, causing a foreign key constraint violation. With cascade, SQLAlchemy issues
`DELETE FROM chunks WHERE document_id = ?` before deleting the document row.

**Forward references:** `Mapped[list["Chunk"]]` uses a string `"Chunk"` because `Chunk` is
defined after `Document` in the file. Python resolves string annotations lazily — by the time
SQLAlchemy needs them, all classes are defined.

---

### 4.4 Default Values — Why Use a Lambda

**Concept:** SQLAlchemy column defaults that should produce a new value per row must be a
callable (function or lambda), not a fixed value. A fixed value is evaluated once at class
definition time.

**Reference:** [backend/models/document.py](backend/models/document.py), [backend/models/session.py](backend/models/session.py)

```python
# ❌ Wrong — uuid.uuid4() is called ONCE when the class is defined
#    Every document gets the same ID
id = mapped_column(String, primary_key=True, default=str(uuid.uuid4()))

# ✅ Correct — lambda is called fresh for each new row
id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
```

**Same issue with `datetime.utcnow`:**
```python
# ❌ Wrong — evaluates once at class definition; all rows get the same timestamp
created_at = mapped_column(DateTime, default=datetime.utcnow())

# ✅ Correct — callable, evaluated per row
created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
#                                                                ↑ no () — passing the function itself
```

This is a classic Python gotcha with mutable or dynamic default values — also seen in function
default argument bugs (`def foo(x=[])` — the list is shared across all calls).

---

### 4.5 Background Task Session Isolation

**Concept:** A FastAPI route's DB session (from `Depends(get_db)`) is scoped to the HTTP
request. Once the response is sent, the session is closed. A background task runs *after* the
response — so it cannot use the request's session. It must open its own.

**Reference:** [backend/api/documents.py](backend/api/documents.py) — `_run_ingestion()`

```python
# ❌ Wrong — db session is closed by the time the background task runs
@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    background_tasks.add_task(_run_ingestion, db=db, ...)   # db will be closed!

# ✅ Correct — background task opens its own session from the factory directly
async def _run_ingestion(...):
    async with AsyncSessionLocal() as db:   # fresh session, owned by this task
        ...
```

**`AsyncSessionLocal`** is the `async_sessionmaker` created in `db/base.py`. Importing and
calling it directly (outside of `Depends`) is the right pattern for code that runs outside a
request context — background tasks, startup hooks, CLI scripts, Celery workers.

**Lifecycle summary:**
```
Request arrives → get_db() yields session → route handler runs → response sent
                                                                       ↓
                                                        session closed (get_db cleanup)
                                                        background task starts
                                                        → opens its own AsyncSessionLocal()
                                                        → does DB work
                                                        → closes its own session
```

---

## 5. Logging & Observability

---

### 5.1 Python Logging Architecture — The Hierarchy

**Concept:** Python loggers form a dotted-name tree. A logger named `backend.api.documents`
is a child of `backend.api`, which is a child of `backend`, which is a child of the root logger.
Log records propagate up the tree until a logger with `propagate=False` stops them.

**Reference:** [backend/logging_config.py](backend/logging_config.py)

```
root logger
  └── backend               ← LOG_LEVEL (e.g. INFO)
        ├── backend.api
        │     └── backend.api.documents
        ├── backend.services
        │     ├── backend.services.llm_provider
        │     └── backend.services.vector_store
        └── backend.agent
              └── backend.agent.nodes
```

**Key points:**
- Every `logging.getLogger(__name__)` in a module creates (or reuses) the logger at that dotted path
- Setting level on `backend` is enough — all children inherit it without individual configuration
- `propagate=False` on `backend` means its records don't reach the root logger's handler a second time
- Root logger is set to `WARNING` to suppress SQLAlchemy, httpx, chromadb SDK noise

**Why `__name__` is the right argument:**
```python
# In backend/services/ingestion.py:
logger = logging.getLogger(__name__)
# __name__ == "backend.services.ingestion" — automatically placed in the right hierarchy
```

---

### 5.2 dictConfig — Configuring Logging Declaratively

**Concept:** `logging.config.dictConfig()` configures the entire logging system from a single
dictionary. It's the preferred approach over multiple `logging.setLevel()` / `addHandler()` calls
because it's atomic, reproducible, and readable as data.

**Reference:** [backend/logging_config.py](backend/logging_config.py) — `configure_logging()`

```python
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,   # ← important: don't wipe loggers created at import time
    "formatters": {
        "default": {"format": "%(asctime)s [%(levelname)s] %(name)s [%(request_id)s] — %(message)s"}
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "stream": "ext://sys.stdout", "formatter": "default"}
    },
    "loggers": {
        "backend": {"level": "INFO", "handlers": ["console"], "propagate": False}
    },
    "root": {"level": "WARNING", "handlers": ["console"]},
})
```

**`disable_existing_loggers: False`** — without this, any logger that was created before
`dictConfig` is called (e.g. at module import time) would be silently disabled. Always set to `False`.

**`ext://sys.stdout`** — the `ext://` prefix tells dictConfig to look up the object in
the Python namespace rather than treating it as a string. `sys.stdout` is the actual stream object.

---

### 5.3 warnings vs logging — Two Separate Systems

**Concept:** Python has two completely independent systems for reporting issues:
- `logging` — for application-level events. Controlled by logger hierarchy and handlers.
- `warnings` — for deprecation notices and usage advisories from libraries. Controlled by `warnings.filterwarnings()`.

**Reference:** [backend/logging_config.py](backend/logging_config.py) — `configure_logging()`

```python
# pypdfium2 does this internally:
import warnings
warnings.warn("get_text_range() will be redirected to get_text_bounded()", UserWarning)
# This goes to stderr directly — it completely bypasses the logging system.
# Setting root logger to WARNING has zero effect on it.
```

**Fix:**
```python
import warnings
warnings.filterwarnings(
    "ignore",
    message=r"get_text_range\(\)",
    category=UserWarning,
    module=r"pypdfium2\._helpers.*",
)
```

**Why this matters:** When you see log output from a library that you can't suppress by adjusting
log levels — it's using `warnings.warn()`, not `logging`. The fix is always `filterwarnings`, not logger configuration.

**Scope the filter tightly:** Use `module=` to match only the library that emits the warning.
A broad `warnings.filterwarnings("ignore", category=UserWarning)` would suppress useful warnings
from your own code and other libraries.

---

### 5.4 exception() vs error() — When to Print a Traceback

**Concept:** `logger.exception()` logs the message *and* appends the full traceback of the current
exception (including `__cause__` chains). `logger.error()` logs only the message. The rule for
when to use each maps directly to whether the exception is expected or not.

**Reference:** [backend/api/documents.py](backend/api/documents.py) — `_run_ingestion()`, [backend/main.py](backend/main.py) — exception handlers

```python
except DocuSenseError as exc:
    # Typed, handled — the class name + message tell the full story.
    # "LLMError: OpenAI embedding request failed: Connection error." is self-contained.
    # A traceback adds noise, not information.
    logger.error(
        "Ingestion failed [%s] — document_id=%s: %s",
        type(exc).__name__, document_id, exc
    )

except Exception:
    # Unexpected — we don't know what went wrong. The stack is the only evidence.
    logger.exception(
        "Unexpected ingestion error — document_id=%s", document_id
    )
```

**The rule:**

| Situation | Method | Traceback? |
|---|---|---|
| Caught a typed `DocuSenseError` | `logger.error()` | ✗ — message is enough |
| Caught bare `Exception` | `logger.exception()` | ✓ — need stack to diagnose |
| Critical startup failure | `logger.critical(..., exc_info=True)` | ✓ — unexpected, need full context |
| Global handler for untyped `Exception` | `logger.error(..., exc_info=True)` | ✓ — unexpected |

**`raise X from exc`** — the `from exc` clause in `raise LLMError(...) from exc` stores the
original exception as `__cause__`. `logger.exception()` prints this full chain, so even without
a traceback at the API layer, the original cause is preserved for server-side debugging when you
need it.

---

### 5.5 Custom Exception Hierarchies

**Concept:** Define domain-specific exception classes that carry typed context. This lets callers
catch by type (not by message string) and lets the logging layer produce clean, self-describing
error messages without needing to inspect the raw third-party exception.

**Reference:** [backend/exceptions.py](backend/exceptions.py)

```python
class DocuSenseError(Exception): pass

class LLMError(DocuSenseError):
    def __init__(self, message: str, *, provider: str = "", operation: str = ""):
        super().__init__(message)
        self.provider = provider      # structured context, not jammed into the string
        self.operation = operation
```

**Why keyword-only context fields (`*`):**
```python
# ❌ Positional — callers must remember argument order
raise LLMError("msg", "claude", "complete")

# ✅ Keyword-only — self-documenting at the call site
raise LLMError("msg", provider="claude", operation="complete")
```

**The wrapping pattern — `raise X from exc`:**
```python
try:
    response = await self._client.messages.create(...)
except Exception as exc:
    raise LLMError(
        f"Claude API request failed: {exc}",   # human-readable, safe to log/surface
        provider="claude",
        operation="complete",
    ) from exc   # ← preserves original exception as __cause__ for server-side debugging
```

**`str(exc)` is the log message:** Because `super().__init__(message)` is called, `str(exc)`
returns exactly the human-readable message. The global exception handler uses `str(exc)` directly
in the JSON response body — it's safe because service-layer code never puts sensitive info in these messages.

---

## 6. AI Engineering Concepts

---

### 6.1 RAG — Retrieval-Augmented Generation


**Concept:** Give an LLM access to your documents at query time — without fine-tuning or retraining.
Retrieve the relevant text, inject it into the prompt, and let the LLM answer from that context.

**Reference:** Overall system flow — [backend/api/chat.py](backend/api/chat.py) → [backend/agent/graph.py](backend/agent/graph.py)

```
User question
     ↓
Embed question → find similar chunks in ChromaDB
     ↓
Inject chunks into LLM prompt as context
     ↓
LLM answers using only that context, with citations
```

**Why not fine-tuning?**
- Fine-tuning bakes knowledge into model weights — can't update without retraining
- RAG retrieves fresh data at query time — documents can be added/removed anytime
- Fine-tuning is expensive; RAG costs only API calls + vector DB storage

**The naive RAG pipeline:** embed → retrieve → stuff → generate.
DocuSense improves on this with an extra grading step — see §5.4.

---

### 6.2 Embeddings and Vector Search

**Concept:** An embedding model converts text into a list of floats (a vector) that encodes
semantic meaning. Similar meanings produce vectors that are close together in the vector space.
A vector database stores these and efficiently finds the closest ones to a query vector.

**Reference:** [backend/services/vector_store.py](backend/services/vector_store.py), [backend/services/ingestion.py](backend/services/ingestion.py)

```
"What is the capital of France?"  →  [0.21, -0.54, 0.88, ...]
"Paris is the capital city"       →  [0.23, -0.51, 0.85, ...]  ← close (similar meaning)
"How to bake a cake?"             →  [-0.71, 0.12, -0.34, ...]  ← far (different meaning)
```

**ChromaDB** stores these vectors and answers: "given this query vector, what are the top_k
closest stored vectors?" — this is Approximate Nearest Neighbour (ANN) search.

**Why Claude can't embed:** Claude is a generative (decoder-only) model. Embedding models are
encoder-only (like BERT). Different architecture, different job. That's why `LLM_PROVIDER`
and `EMBEDDING_PROVIDER` are configured separately — see [backend/config.py](backend/config.py) and `CLAUDE.md §3.3`.

**One collection per document:** ChromaDB collections are namespaced as `doc_{uuid}` (see
`_collection_name()` in [backend/services/vector_store.py](backend/services/vector_store.py)). When querying, the API passes
`document_ids` to scope the search to specific documents — multi-tenancy handled at the API layer.

---

### 6.3 Chunking Strategy

**Concept:** Documents are split into smaller pieces (chunks) before embedding. Each chunk gets
its own vector. Querying returns chunks, not whole documents.

**Reference:** [backend/services/ingestion.py](backend/services/ingestion.py) — constants at top of file

```python
CHUNK_SIZE = 500    # tokens
CHUNK_OVERLAP = 50  # tokens
```

**Why chunk?**
- Embedding a whole 50-page PDF produces one vector — too coarse, loses specificity
- Smaller chunks → more precise retrieval — the exact paragraph is returned, not the whole section
- LLM context windows are limited — you can't stuff an entire document in a prompt

**Why overlap?** A fact that spans a chunk boundary (last sentence of chunk N, first of chunk N+1)
would be split and potentially lost. With 50-token overlap, the tail of chunk N appears at the
head of chunk N+1 — continuity is preserved.

**`RecursiveCharacterTextSplitter`** (from LangChain) tries to split at natural boundaries:
paragraph breaks → sentence breaks → word breaks → character breaks. It only falls to the next
level if the current level can't produce chunks of the right size. This preserves readability
better than naive character splitting.

**Changing chunk size:** Requires re-embedding all documents (different chunks = different vectors).
`EMBEDDING_VERSION` in [backend/services/ingestion.py](backend/services/ingestion.py) tracks this — a version bump signals
that re-ingestion is needed. See `CLAUDE.md §6.4`.

---

### 6.4 LangGraph — Agent Graph vs. Chain

**Concept:** A **chain** is linear: A → B → C. A **graph** (LangGraph) has named nodes, typed
shared state, and explicit edges. Each node is independently inspectable and testable.

**Reference:** [backend/agent/graph.py](backend/agent/graph.py), [backend/agent/nodes.py](backend/agent/nodes.py), [backend/agent/state.py](backend/agent/state.py)

```
retrieve → grade_docs → generate → END
```

**Why a graph instead of a chain (from CLAUDE.md §3.1):**

1. **Observability:** In a chain, if the answer is wrong, you can't tell whether retrieval or
   generation failed. Named nodes are independently logged — you can see exactly what `retrieve`
   returned and whether `grade_docs` filtered it correctly.

2. **The grading node:** Semantic similarity (vector search) finds chunks that are topically
   related but not always specifically useful. `grade_docs` runs each chunk through an LLM with
   a binary yes/no prompt — a second, smarter filter that reduces hallucination.

**Shared state — `AgentState`:**
```python
# Each node reads from state and returns a partial update
async def grade_docs(state: AgentState, ...) -> dict:
    ...
    return {"graded_chunks": graded}   # only updates this key; rest of state untouched
```

LangGraph merges partial returns into the shared state — no node needs to copy the parts of
state it didn't touch.

**v2 topology (implemented):** When `grade_docs` filters out all chunks, instead of returning
an empty answer the graph loops back via a conditional edge — see §5.8 and §5.9:
```
retrieve → grade_docs → [router] → generate → END
                            ↓  (graded_chunks empty AND rewrite_count < 2)
                       rewrite_query → retrieve
```

---

### 6.5 Prompt Engineering as Code

**Concept:** Prompts are code — they should be version-controlled, centralised, documented,
and treated as a first-class engineering artefact.

**Reference:** [backend/agent/prompts.py](backend/agent/prompts.py)

**Patterns used:**

**① Centralise all prompts in one file** — changes are visible in one diff; contradictions are
caught by reading them together.

**② Constrain output format to simplify parsing:**
```python
GRADE_SYSTEM = """...
Rules:
- Output exactly one word: yes or no.
- Do not explain. Do not hedge. Do not output punctuation."""
```
The node parses with `response.strip().lower() == "yes"`. If the prompt allowed "Yes, this chunk
is relevant", the parse would fail. Engineering the output shape is as important as engineering
the reasoning.

**③ Parametrised templates:**
```python
GRADE_USER = """Question: {question}

Document chunk:
{chunk_content}

Is this chunk relevant?"""

# Node fills in variables
GRADE_USER.format(question=state["question"], chunk_content=chunk["content"])
```
Template (what you tune) is separated from data (what varies per request).

**④ Inline tuning notes** explain *why* each rule exists and *how* to adjust it:
```python
# Tweak: If too many relevant chunks are filtered, soften:
# "contains information directly relevant" → "may be relevant"
```
This makes prompt changes deliberate and reversible.

**⑤ Citation format is a contract:** The `[filename, p.N]` format in `GENERATE_SYSTEM` is
parsed by `SourceCard.tsx` on the frontend. `CLAUDE.md §6.6` explicitly records this coupling —
changing one requires changing the other.

---

### 6.6 Provider Abstraction — Swappable LLMs

**Concept:** The rest of the application only ever calls `provider.complete(system, user)` — it
has no knowledge of which LLM is underneath. Switching providers is a config change, not a
code change.

**Reference:** [backend/services/llm_provider.py](backend/services/llm_provider.py) (Protocol + all provider classes),
[backend/agent/nodes.py](backend/agent/nodes.py) (nodes only call `chat_provider.complete()`),
[backend/agent/graph.py](backend/agent/graph.py) (providers injected via `functools.partial`)

```
Config: LLM_PROVIDER=claude
         ↓
get_chat_provider(settings) → ClaudeProvider
         ↓
build_graph(chat_provider=ClaudeProvider(...))
         ↓
grade_docs node: await chat_provider.complete(...)   ← no mention of Claude
generate node:   await chat_provider.complete(...)   ← no mention of Claude
```

**MockProvider for development:**
```python
class MockChatProvider:
    async def complete(self, system: str, user: str) -> str:
        if "yes" in system.lower() or "no" in system.lower():
            return "yes"
        return "This is a mock answer."
```
Set `USE_MOCK_LLM=true` and the entire pipeline runs without any API keys or API credits.
Indispensable for rapid iteration and testing.

---

### 6.7 PDF Text Extraction — Why Library Choice Matters

**Concept:** PDFs don't store text — they store drawing instructions ("place glyph X at position Y").
A text extraction library must infer word boundaries, reading order, and spacing from those
coordinates. Different libraries do this with very different quality.

**Reference:** [backend/services/ingestion.py](backend/services/ingestion.py) — `parse_document()`

**Why this matters for RAG:** If the extracted text has words joined together (`"thereforethe"`
instead of `"therefore the"`), the embedding is degraded — the tokeniser splits at unexpected
boundaries, and semantic similarity search works on corrupted input. Garbage in, garbage out.

**Benchmark findings** ([py-pdf/benchmarks](https://github.com/py-pdf/benchmarks)):

| Library | Quality | Speed | Notes |
|---|---|---|---|
| pypdfium2 | 97% | 0.1s | Google PDFium engine (used in Chrome). Best choice. |
| PyMuPDF | 96% | 0.1s | Excellent, but AGPL licence |
| pypdf | 96% | 3.5s | Pure Python — good quality but 35× slower; spacing issues on some PDFs |
| pdfplumber | 75% | 9.5s | Worst of both: slow AND low quality |

**Why pypdfium2 was chosen:** Best quality score, fastest, permissive Apache 2.0 licence.
`pypdf` was the original choice and produced the same 96% benchmark score, but had real-world
word-joining issues on the test PDF — the benchmark average hid per-document variance.

**The pymupdf4llm alternative:** Outputs Markdown (headings, tables) instead of plain text.
Useful if you want structure-aware chunking. Rejected for v1 because markdown syntax (`##`, `**`)
ends up embedded in chunk text sent to the LLM, adding noise without a complementary
markdown-aware chunking strategy.

**API:**
```python
import pypdfium2

pdf = pypdfium2.PdfDocument(str(file_path))
for i, page in enumerate(pdf, start=1):
    textpage = page.get_textpage()
    text = textpage.get_text_range()
```

---

### 6.8 LangGraph Conditional Edges — Routing Between Nodes at Runtime

**Concept:** `add_conditional_edges()` lets a node's output determine which node runs next.
A **router function** reads the current state and returns a string key that maps to the next node.
This is how you implement branching, loops, and early exits in a LangGraph agent.

**Reference:** [backend/agent/graph.py](backend/agent/graph.py) — `_route_after_grade`, `add_conditional_edges`

```python
MAX_REWRITES = 2

def _route_after_grade(state: AgentState) -> str:
    """After grade_docs: loop back to rewrite if nothing passed, else generate."""
    if not state["graded_chunks"] and state["rewrite_count"] < MAX_REWRITES:
        return "rewrite_query"
    return "generate"

# Wire it into the graph
graph.add_conditional_edges(
    "grade_docs",                          # source node
    _route_after_grade,                    # router function (state → str)
    {
        "rewrite_query": "rewrite_query",  # key → node name
        "generate":      "generate",
    },
)
graph.add_edge("rewrite_query", "retrieve")  # close the loop
```

**Compare with a static edge:**
```python
# Static — always goes to generate
graph.add_edge("grade_docs", "generate")

# Conditional — runtime decision
graph.add_conditional_edges("grade_docs", router_fn, {"a": "node_a", "b": "node_b"})
```

**The router function is pure:** It reads state and returns a string — no side effects.
This makes the routing logic easy to unit-test independently of the nodes themselves:
```python
assert _route_after_grade({"graded_chunks": [], "rewrite_count": 0}) == "rewrite_query"
assert _route_after_grade({"graded_chunks": [], "rewrite_count": 2}) == "generate"
assert _route_after_grade({"graded_chunks": [chunk], "rewrite_count": 0}) == "generate"
```

**Module-level constant for the cap:** `MAX_REWRITES = 2` is defined at the top of `graph.py`.
Making it a named constant rather than an inline `< 2` means there is one place to change it,
and it's self-documenting at the usage site.

---

### 6.9 Agentic Loop Pattern — Query Rewriting with a Max-Retry Cap

**Concept:** In an agentic system, when a step fails (all chunks graded irrelevant), the agent
can *try again differently* rather than giving up. But unbounded retries cause infinite loops —
a counter in shared state caps iterations and guarantees termination.

**Reference:** [backend/agent/nodes.py](backend/agent/nodes.py) — `rewrite_query`, [backend/agent/graph.py](backend/agent/graph.py)

```
Attempt 1: question = "what is the return policy?"
  → retrieve (top-5 chunks) → grade_docs (all filtered out)
  → rewrite_count=0 < 2, so → rewrite_query

Attempt 2: question = "refund terms and conditions"  ← reformulated
  → retrieve (new top-5) → grade_docs (2 chunks pass)
  → graded_chunks non-empty → generate → answer ✅

Worst case (both rewrites fail):
  → rewrite_count=2, graded_chunks=[] → generate → fallback answer
```

**The `rewrite_query` node clears stale state:**
```python
return {
    "question": rewritten,
    "rewrite_count": state["rewrite_count"] + 1,
    "retrieved_chunks": [],   # ← must clear or retrieve sees the old chunks
    "graded_chunks": [],      # ← must clear or grade_docs sees old (failed) results
}
```
LangGraph merges partial state updates — you only need to return keys that change.
Clearing these ensures `retrieve` starts fresh with the new question.

**Why the counter lives in `AgentState`:**
State is the only thing shared between nodes in a LangGraph graph. There is no other place to
store per-run counters — no globals, no external DB writes mid-graph (CLAUDE.md §6.2).

**Termination guarantee:** The router checks `rewrite_count < MAX_REWRITES` before routing to
`rewrite_query`. Once the cap is hit, `generate` always runs. `generate` handles empty
`graded_chunks` gracefully (returns a "documents don't contain enough information" fallback).
The graph always terminates.

**General principle — agentic loops need exit conditions:** Any loop in an agent graph must
have a guaranteed termination condition that doesn't depend on the LLM behaving correctly.
An LLM that always rewrites to something irrelevant would loop forever without the counter.

---

## 7. Software Engineering Principles & Design Patterns

> These are general principles, grounded in decisions made in this codebase.
> Each entry ties theory to concrete code so it's easier to internalise and recall.

---

### 7.1 Fail Fast vs Graceful Degradation

**Concept:** Two opposing strategies for handling failures — which to use depends on whether
a partial result is better than no result.

**Fail fast:** Crash immediately with a clear error. Used when continuing would produce
wrong results silently or corrupt state.

**Graceful degradation:** Continue with reduced functionality. Used when partial results
are still useful and the failure is isolated.

**In DocuSense:**

| Situation | Strategy | Reasoning |
|---|---|---|
| DB unreachable at startup | Fail fast (`sys.exit(1)`) | App can't serve any request correctly — better to crash clearly than serve silent 500s |
| Bad `LLM_PROVIDER` env var | Fail fast (CRITICAL log + raise) | Misconfiguration — every request will fail, signal it immediately |
| LLM fails for one chunk in `grade_docs` | Graceful degradation (skip, continue) | Other chunks may still be relevant — partial answer beats an error page |
| LLM fails in `generate` | Fail fast (`AgentError`) | Generation is the entire point — a silent empty response is worse than an explicit error |
| ChromaDB collection missing on delete | Graceful degradation (log WARNING, return 204) | Best-effort cleanup — document is removed from Postgres regardless |

**Reference:** [backend/main.py](backend/main.py) — startup, [backend/agent/nodes.py](backend/agent/nodes.py) — `grade_docs` vs `generate`

**Interview answer:** "Fail fast for misconfiguration and unrecoverable state; degrade gracefully
when partial results are better than nothing and the failure is isolated to one component."

---

### 7.2 Defense in Depth — Layered Error Handling

**Concept:** Multiple independent error-handling layers, each narrower in scope. If an inner
layer misses something, the outer layer catches it. No single layer is solely responsible for
catching everything.

**Reference:** All backend layers

```
[Service layer]      Wraps third-party exceptions → LLMError, VectorStoreError, IngestionError
        ↓ propagates if not caught
[API layer]          Catches DocuSenseError, marks doc failed, sends HTTP response
        ↓ propagates if not caught
[Global handler]     Exception → "An unexpected error occurred" — nothing leaks to client
```

**Each layer has a single job:**
- **Service layer** — wraps library exceptions into typed domain errors with context. Has no knowledge of HTTP status codes.
- **API layer** — handles domain errors, updates system state (doc status), decides HTTP semantics.
- **Global handler** — last line of defence. Ensures *nothing* escapes as an unformatted 500.

**Analogy:** Castle walls. Even if an attacker breaches the outer wall (a library exception
propagates past the service layer), there's an inner wall (API catch), then a keep (global handler).
Each layer is independently valuable.

---

### 7.3 Chain of Responsibility Pattern

**Concept:** A request (or exception) passes through a chain of handlers. Each handler either
handles it fully or passes it to the next. No handler needs to know about the full chain.

**Reference:** Error propagation across [backend/services/ingestion.py](backend/services/ingestion.py) → [backend/api/documents.py](backend/api/documents.py) → [backend/main.py](backend/main.py)

```
pypdfium2 raises OSError
   → parse_document() catches it, raises IngestionError("Failed to parse 'report.pdf': ...")
      → ingest() lets IngestionError propagate (already typed, nothing to add)
         → _run_ingestion() catches DocuSenseError, logs clean ERROR, marks doc failed
            → (if bare Exception, global handler in main.py returns safe JSON 500)
```

**Classic Gang of Four description:** A chain of receiver objects. Each decides whether to
handle a request or pass it to the next in the chain.

**The key contribution of each link:** Each handler adds *context and type* as the exception
moves up the stack. The final handler sees a rich `IngestionError("Failed to parse 'report.pdf'...")`
rather than a raw `OSError: [Errno 22] Invalid argument`.

---

### 7.4 Separation of Concerns

**Concept:** Each module does one thing and has one reason to change. Mixing concerns produces
code that is hard to test, reason about, and modify independently.

**Reference:** Demonstrated by the deliberate boundaries across the backend

**Applied in this codebase:**

| Concern | Where it lives | Deliberately excluded from |
|---|---|---|
| LLM API calls | `services/llm_provider.py` | HTTP status codes, DB operations |
| Exception taxonomy | `exceptions.py` | Zero app imports — no circular dependencies possible |
| Logging setup | `logging_config.py` | Does NOT import `Settings` — reads raw `os.environ` to avoid import-order issues |
| HTTP error formatting | `main.py` global handlers | No knowledge of which layer caused the error |
| Ingestion logic | `services/ingestion.py` | Has no access to the HTTP request that triggered it |
| DB session lifecycle | `db/base.py` + `get_db()` | Route handlers never call `session.close()` |

**One subtle example:** `logging_config.py` reads `os.environ.get("LOG_LEVEL")` directly instead
of importing `Settings`. If it imported `Settings`, then logging setup would depend on
pydantic-settings, which might emit unformatted log lines before `configure_logging()` finishes.
Keeping the module import-free means it can always be the first thing that executes.

---

### 7.5 The 12-Factor App Methodology

**Concept:** 12 principles for building portable, deployable software-as-a-service.
Originally from Heroku (2011), now industry-standard. Knowing them is expected in senior
engineering conversations and system design interviews.

**Reference:** [backend/config.py](backend/config.py), [backend/logging_config.py](backend/logging_config.py), [docker-compose.yml](docker-compose.yml)

**Most important factors, applied in DocuSense:**

| # | Factor | Principle | How it's applied |
|---|---|---|---|
| III | Config | Store config in env vars, not code | `pydantic-settings` reads all config from env; nothing hardcoded |
| IV | Backing services | Treat DB, cache, etc. as attached resources | `DATABASE_URL`, `CHROMA_HOST` — swappable via env without code change |
| VI | Processes | Stateless processes | No shared in-memory state between requests |
| XI | Logs | Treat logs as event streams — write to stdout | `StreamHandler` to stdout only; Docker handles routing and retention |

**Factor XI is the direct justification for the no-file-handler decision:** A process should not
concern itself with routing or storage of its output stream. Write to stdout; let the execution
environment (Docker, systemd, a log aggregator) decide what to do with it.

**Interview tip:** Factor XI also explains why you don't `tail -f app.log` in production —
you query a log aggregator (Datadog, Splunk, CloudWatch) that ingests stdout from all instances.

---

### 7.6 Observability in System Design

**Concept:** Observability is the ability to understand what a system is doing from the outside,
through its outputs. The three pillars are **logs**, **metrics**, and **traces**.

| Pillar | Question it answers | Example |
|---|---|---|
| **Logs** | "What happened?" — discrete events | `ERROR: LLMError [provider=claude]: Connection refused` |
| **Metrics** | "How is it performing?" — aggregated numbers | `p99 ingestion latency = 4.2s`, `embedding calls/min = 12` |
| **Traces** | "Where did the time go?" — per-request timing breakdown | `total=820ms: parse=40ms, embed=510ms, upsert=270ms` |

DocuSense v1 implements **logs only**. Metrics and traces are out of scope but the groundwork
is laid: structured logs with `request_id` can be parsed by a log aggregator to approximate
both (e.g. latency extracted from log timestamps, per-request traces reconstructed from `request_id`).

**Log levels as a system design decision:**

| Level | Meaning | When to use |
|---|---|---|
| DEBUG | Internal state detail | Chunk counts, embedding dims — too noisy for production |
| INFO | Lifecycle milestones | Request accepted, ingestion complete — always-on in production |
| WARNING | Degraded but recoverable | Chunk graded irrelevant, collection not found on delete |
| ERROR | Handled failure that changed behaviour | Document marked failed |
| CRITICAL | System cannot continue | DB unreachable at startup |

**Structured logging upgrade path:** Plain text logs are fine for a single service. At scale,
switch to JSON (`LOG_FORMAT=json`) so a log aggregator can filter by field:
`level=ERROR AND provider=claude`. DocuSense supports this today — zero code change, just an env var.

---

### 7.7 Open/Closed Principle Applied to Error Hierarchies

**Concept:** From SOLID — software entities should be **open for extension, closed for modification**.
Adding new behaviour should not require changing existing code.

**Reference:** [backend/exceptions.py](backend/exceptions.py), [backend/main.py](backend/main.py) — global handler

**The global handler catches `DocuSenseError`:**
```python
@app.exception_handler(DocuSenseError)
async def docusense_error_handler(request, exc: DocuSenseError):
    return JSONResponse(status_code=500, content={
        "error": type(exc).__name__,   # automatically uses the subclass name
        "detail": str(exc),
    })
```

Adding `RateLimitError(LLMError)` in the future requires:
- Add the class to `exceptions.py` ✅ — extension
- Raise it in `llm_provider.py` when rate-limited ✅ — extension
- The global handler automatically formats it ✅ — zero modification

To give it a `429` status code instead of `500`, register *one additional* handler:
```python
@app.exception_handler(RateLimitError)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, ...)
```

The broader principle: design abstraction boundaries so that the *common case* (new subtype of
an existing concept) requires adding code, not changing existing code.

---

### 7.8 Correlation IDs — Tracing Requests Across Layers

**Concept:** Assign a unique ID to each request at entry and attach it to every log line produced
during that request — across all layers. Enables reconstructing the full lifecycle of any single
request by filtering on its ID.

**Reference:** [backend/main.py](backend/main.py) — `request_id_middleware`, `_request_id_var`, `_RequestIdFilter`

**In DocuSense (single service):**
```
15:22:10 [INFO]  backend.api.documents      [req-f4a1b2] — Document accepted — id=abc-123
15:22:10 [DEBUG] backend.services.ingestion [req-f4a1b2] — ingest start — chunks=47
15:22:11 [DEBUG] backend.services.vector_store [req-f4a1b2] — Connecting to ChromaDB
15:22:11 [ERROR] backend.api.documents      [req-f4a1b2] — Ingestion failed [VectorStoreError]: ...
```
`grep "req-f4a1b2"` → full story in order, across all layers.

**In microservices (system design context):**
The same ID is forwarded as an HTTP header (`X-Request-ID`, `X-Trace-ID`) to every downstream
service. Each service logs it. You reconstruct a distributed trace with nothing more than logs —
no dedicated tracing infrastructure required at small scale.

**Standard practice:**
1. Generate at the entry point (API gateway or first service)
2. Store in request-scoped context (`ContextVar` in Python, `AsyncLocalStorage` in Node)
3. Stamp every log line via a `Filter` or log formatter
4. Forward in outbound HTTP headers to downstream services
5. Echo in the HTTP response (`X-Request-ID`) so clients can include it in bug reports

**Why this matters in system design interviews:** When asked "how would you debug a latency spike
in a distributed system?", correlation IDs are step one — before metrics, before profiling.
You need to identify *which requests* are slow before you can understand *why* they're slow.

---

## 8. Frontend Development — React + Vite + TypeScript

---

### 8.1 Vite Dev Server + Docker — The Host Binding Problem

**Concept:** When running inside a Docker container, a dev server must bind to `0.0.0.0`
(all interfaces), not `localhost` / `127.0.0.1`. Docker's port mapping forwards traffic from
the host to the container's network interface — but `localhost` inside a container only
accepts connections *from within the same container*, not from Docker's bridge network.

**Reference:** [frontend/vite.config.ts](frontend/vite.config.ts)

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",   // ← accepts connections from outside the container
    port: 3000,
    strictPort: true,   // fail immediately if 3000 is taken (don't silently try 3001)
  },
});
```

**What went wrong without this:**
```
Container: Vite listens on 127.0.0.1:5173
Docker maps: host:3001 → container:3000
Result: port 3000 inside container has nothing listening → connection refused on host:3001
```

**Symptoms that point to this bug:**
- Container shows `Local: http://localhost:5173/` but no `Network:` line
- `docker compose ps` shows port mapping (e.g. `3001->3000`) but browser can't connect
- The server is running fine inside the container — just not reachable from outside

**The same rule applies to any dev server run in Docker:** Flask, Django, Express, FastAPI —
always check for a `--host 0.0.0.0` flag or equivalent config option.

**Vite default port is 5173** — the Dockerfile exposed 3000 but Vite wasn't using it. Two bugs
at once: wrong host binding AND wrong port. The `vite.config.ts` fixes both.

---

### 8.2 Typed Axios Client Pattern

**Concept:** Centralise all API calls in a single typed module. Route components call named
functions with typed arguments and get typed return values — they never see URLs, headers, or
status codes.

**Reference:** [frontend/src/api/client.ts](frontend/src/api/client.ts)

```typescript
// One Axios instance with the base URL — change this one place to point at prod
const http = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000" });

// Typed interfaces matching the backend Pydantic response models
export interface DocumentRecord {
  id: string;
  name: string;
  status: "pending" | "processing" | "complete" | "failed";
  chunk_count: number;
  created_at: string;
}

// Named function — callers never construct URLs
export async function listDocuments(): Promise<DocumentRecord[]> {
  const res = await http.get<DocumentRecord[]>("/api/documents/");
  return res.data;
}
```

**`import.meta.env.VITE_API_URL`** — Vite injects env vars prefixed with `VITE_` from `.env`
files and the container's `process.env`. At runtime in the browser, they are replaced by their
values at build/dev-server start time. Variables without the `VITE_` prefix are stripped for
security (never exposed to the browser).

**Why a typed client over raw `fetch`:**
- Centralised base URL and auth headers
- TypeScript catches API shape mismatches at compile time
- Mocking in tests: replace the client module, not individual `fetch` calls
- If an endpoint URL changes, update one function — not every component

---

### 8.3 React Hooks for Async State

**Concept:** React's built-in hooks manage state and side effects in function components.
For async data fetching, the common pattern is: `useState` for the data, `useEffect` to
trigger the fetch, `useCallback` to memoize the fetch function.

**Reference:** [frontend/src/pages/Chat.tsx](frontend/src/pages/Chat.tsx)

```typescript
const [documents, setDocuments] = useState<DocumentRecord[]>([]);  // state
const [loading, setLoading] = useState(false);

// useCallback memoizes fetchDocs — same function reference across renders
// so useEffect's dependency array stays stable (avoids infinite re-fetching)
const fetchDocs = useCallback(async () => {
  const docs = await listDocuments();
  setDocuments(docs);
}, []);  // empty deps = created once

useEffect(() => {
  fetchDocs();   // run on mount
}, [fetchDocs]);
```

**Hook summary:**

| Hook | Purpose | When to use |
|---|---|---|
| `useState<T>(init)` | Store a value, re-render on change | Any piece of UI state |
| `useEffect(fn, deps)` | Run a side effect after render | Fetching data, subscriptions, timers |
| `useCallback(fn, deps)` | Memoize a function reference | Stabilise deps for `useEffect` / child props |
| `useRef<T>()` | Mutable ref, no re-render on change | DOM access (`inputRef.current.focus()`), timers |

**The `deps` array:**
- `[]` — run once (on mount)
- `[a, b]` — re-run when `a` or `b` changes
- No array — run after every render (usually a bug)

**Async in `useEffect`:** `useEffect` cannot be `async` directly — return value must be a
cleanup function or `undefined`, not a Promise. Pattern: define async function inside, call it.
```typescript
useEffect(() => {
  async function load() { await fetchDocs(); }
  load();
}, [fetchDocs]);
// OR: useCallback + direct call as shown above
```

---

### 8.4 Polling with setInterval for Live Status Updates

**Concept:** When a backend operation is async (document ingestion runs in a background task),
the frontend must poll for status changes. `setInterval` schedules repeated calls; the cleanup
function returned from `useEffect` clears the interval when the component unmounts.

**Reference:** [frontend/src/pages/Chat.tsx](frontend/src/pages/Chat.tsx) — `POLL_INTERVAL_MS`

```typescript
const POLL_INTERVAL_MS = 4000;

useEffect(() => {
  fetchDocs();                                          // immediate first fetch
  const id = setInterval(fetchDocs, POLL_INTERVAL_MS); // then every 4s
  return () => clearInterval(id);                      // cleanup on unmount
}, [fetchDocs]);
```

**Why the cleanup matters:** Without `clearInterval`, the timer keeps firing after the component
unmounts — calling `setDocuments` on an unmounted component, which causes a React warning and
a potential memory leak.

**Polling vs WebSocket vs SSE:**

| Approach | Complexity | Latency | Server load | Use when |
|---|---|---|---|---|
| Polling | Low | Up to `interval` | N × `1/interval` req/s | Status changes infrequently, simple setup |
| Server-Sent Events (SSE) | Medium | Near-real-time | One long-lived connection | Server pushes updates (e.g. streaming) |
| WebSocket | High | Real-time | One connection | Bidirectional real-time (e.g. live collaboration) |

Polling at 4s is fine here: ingestion takes 2–10s, and a user seeing "processing" for a few
extra seconds is acceptable. The alternative would be SSE from the backend ingestion task.

---

### 8.5 FormData for File Uploads

**Concept:** HTTP file uploads use `multipart/form-data` encoding — not JSON. The browser
packages the file binary and any other fields into a `FormData` object. The `Content-Type`
header must include the boundary marker (Axios sets this automatically).

**Reference:** [frontend/src/api/client.ts](frontend/src/api/client.ts) — `uploadDocument`

```typescript
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);          // key "file" must match FastAPI's File(...) param name

  const res = await http.post<UploadResponse>("/api/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    // Axios sets the boundary automatically when Content-Type is multipart/form-data
    // If you set it manually WITH a boundary, it will be wrong — let Axios handle it
  });
  return res.data;
}
```

**FastAPI side — matching the key:**
```python
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # "file" here matches form.append("file", ...) in the frontend
```

**`File` input in React:**
```typescript
// Get File object from an <input type="file"> ref
const file = inputRef.current?.files?.[0];
if (file) await uploadDocument(file);
```

**`file.name`, `file.type`, `file.size`** — the `File` object carries metadata. `file.type`
matches MIME types like `"application/pdf"` — the same strings checked in `ALLOWED_TYPES` on
the backend. But always validate on the server too — the browser's MIME detection is advisory.

---

## 9. Changelog

| Date | Phase | What was added |
|---|---|---|
| Project init | Pre-implementation | [§1 Python fundamentals](#1-python-backend-fundamentals), [§2 Async Python](#2-async-python), [§3 FastAPI](#3-fastapi-patterns), [§4 SQLAlchemy](#4-sqlalchemy-orm-v2), [§6 AI Engineering](#6-ai-engineering-concepts) — all from reading the skeleton |
| Phase 1 | Document upload & ingestion | [§2.3 Async factory functions](#23-async-factory-functions--awaitable-constructors), [§3.5 Structured error logging](#35-structured-error-logging--never-swallow-exceptions-silently), [§4.5 Background task session isolation](#45-background-task-session-isolation), [§6.7 PDF extraction library choice](#67-pdf-text-extraction--why-library-choice-matters) |
| 2026-06-08 | Logging & error handling | [§3.6 Global exception handlers](#36-global-exception-handlers--centralised-http-error-responses), [§3.7 ContextVar + logging.Filter](#37-request-scoped-context--contextvar--loggingfilter), [§5 Logging & Observability](#5-logging--observability) (all 5 entries), [§7 SE Principles & Design Patterns](#7-software-engineering-principles--design-patterns) (all 8 entries) |
| 2026-06-10 | Phase 2 — Query pipeline, rewrite loop & frontend | [§3.8 db.flush() vs db.commit()](#38-dbflush-vs-dbcommit--getting-generated-ids-mid-transaction), [§6.8 LangGraph conditional edges](#68-langgraph-conditional-edges--routing-between-nodes-at-runtime), [§6.9 Agentic loop pattern](#69-agentic-loop-pattern--query-rewriting-with-a-max-retry-cap), [§8 Frontend Development](#8-frontend-development--react--vite--typescript) (all 5 entries) |
