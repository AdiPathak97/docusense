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
4. [SQLAlchemy ORM (v2)](#4-sqlalchemy-orm-v2)
   - [4.1 Mapped Annotations — Typed Columns](#41-mapped-annotations--typed-columns)
   - [4.2 Async Engine and asyncpg](#42-async-engine-and-asyncpg)
   - [4.3 Relationships and Cascade Delete](#43-relationships-and-cascade-delete)
   - [4.4 Default Values — Why Use a Lambda](#44-default-values--why-use-a-lambda)
   - [4.5 Background Task Session Isolation](#45-background-task-session-isolation)
5. [AI Engineering Concepts](#5-ai-engineering-concepts)
   - [5.1 RAG — Retrieval-Augmented Generation](#51-rag--retrieval-augmented-generation)
   - [5.2 Embeddings and Vector Search](#52-embeddings-and-vector-search)
   - [5.3 Chunking Strategy](#53-chunking-strategy)
   - [5.4 LangGraph — Agent Graph vs. Chain](#54-langgraph--agent-graph-vs-chain)
   - [5.5 Prompt Engineering as Code](#55-prompt-engineering-as-code)
   - [5.6 Provider Abstraction — Swappable LLMs](#56-provider-abstraction--swappable-llms)
   - [5.7 PDF Text Extraction — Why Library Choice Matters](#57-pdf-text-extraction--why-library-choice-matters)
6. [Changelog](#6-changelog)

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
failures completely. `logger.exception()` logs the full traceback at ERROR level — it captures
the current exception automatically, so you don't need to pass it explicitly.

**Reference:** [backend/api/documents.py](backend/api/documents.py) — `_run_ingestion()`

```python
import logging
logger = logging.getLogger(__name__)   # ← module-level logger, named after the file

async def _run_ingestion(...):
    try:
        ...
    except Exception:
        logger.exception("Ingestion failed for document %s (%s)", document_id, document_name)
        # sets doc.status = failed, then re-raises implicitly via logger
```

**`logger.exception()` vs `logger.error()`:**
- `logger.error("msg")` — logs the message at ERROR level
- `logger.exception("msg")` — logs the message AND appends the full stack trace of the current
  exception. Only valid inside an `except` block.

**`logging.getLogger(__name__)`:**
- `__name__` is the module's dotted import path (e.g. `backend.api.documents`)
- Loggers form a hierarchy by name — `backend.api.documents` inherits config from `backend.api`,
  then `backend`, then the root logger
- This lets you silence or redirect logs from a whole subtree: `logging.getLogger("backend").setLevel(logging.WARNING)`

**The rule:** In background tasks especially, always log before swallowing exceptions — the task
runs outside the request/response cycle, so uncaught exceptions disappear silently otherwise.

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

## 5. AI Engineering Concepts

---

### 5.1 RAG — Retrieval-Augmented Generation

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

### 5.2 Embeddings and Vector Search

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

### 5.3 Chunking Strategy

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

### 5.4 LangGraph — Agent Graph vs. Chain

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

**v2 planned topology:** When `grade_docs` filters out all chunks (nothing is relevant),
instead of returning an empty answer, the graph would loop back:
`grade_docs → rewrite_query → retrieve → grade_docs → ...`
The `REWRITE_SYSTEM`/`REWRITE_USER` prompts are already written in [backend/agent/prompts.py](backend/agent/prompts.py) for this.

---

### 5.5 Prompt Engineering as Code

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

### 5.6 Provider Abstraction — Swappable LLMs

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

### 5.7 PDF Text Extraction — Why Library Choice Matters

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

## 6. Changelog

| Date | Phase | What was added |
|---|---|---|
| Project init | Pre-implementation | [§1 Python fundamentals](#1-python-backend-fundamentals), [§2 Async Python](#2-async-python), [§3 FastAPI](#3-fastapi-patterns), [§4 SQLAlchemy](#4-sqlalchemy-orm-v2), [§5 AI Engineering](#5-ai-engineering-concepts) — all from reading the skeleton |
| Phase 1 | Document upload & ingestion | [§2.3 Async factory functions](#23-async-factory-functions--awaitable-constructors), [§3.5 Structured error logging](#35-structured-error-logging--never-swallow-exceptions-silently), [§4.5 Background task session isolation](#45-background-task-session-isolation), [§5.7 PDF extraction library choice](#57-pdf-text-extraction--why-library-choice-matters) |
