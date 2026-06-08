import logging
import os
import sys
import uuid
from contextvars import ContextVar

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.logging_config import configure_logging

# ── Logging must be configured before anything else so import-time log calls
# from routers / services are already formatted correctly.
configure_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_format=os.environ.get("LOG_FORMAT", "plain"),
)

from backend.api.chat import router as chat_router
from backend.api.documents import router as documents_router
from backend.db.base import Base, engine
from backend.exceptions import DocuSenseError

logger = logging.getLogger(__name__)

# ── Request-ID context variable ───────────────────────────────────────────────
# Each async request gets a fresh UUID injected here. A logging.Filter stamps
# every LogRecord emitted within that request with the same ID so you can grep
# a single request across all service layers.

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class _RequestIdFilter(logging.Filter):
    """Copy the current request_id from the ContextVar onto every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.request_id = _request_id_var.get("")  # type: ignore[attr-defined]
        return True


# Attach the filter to every handler on the 'backend' logger so all app loggers
# pick it up (they propagate to 'backend', which owns the StreamHandler).
_backend_logger = logging.getLogger("backend")
for _handler in _backend_logger.handlers:
    _handler.addFilter(_RequestIdFilter())


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(title="DocuSense", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


# ── Request-ID middleware ─────────────────────────────────────────────────────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Inject a unique request ID into the logging context for every HTTP request.

    The ID is also echoed in the X-Request-ID response header so clients and
    API consumers can correlate their requests with server log lines.
    """
    rid = str(uuid.uuid4())
    token = _request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        _request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(DocuSenseError)
async def docusense_error_handler(
    request: Request, exc: DocuSenseError
) -> JSONResponse:
    """Return a structured JSON error for any typed application exception.

    The message stored in the exception is safe to surface — service-layer code
    must never put API keys, raw SQL, or internal paths in DocuSenseError messages.
    """
    logger.error(
        "DocuSenseError [%s] on %s %s: %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all for any exception not explicitly handled elsewhere.

    Deliberately hides the exception message from the client — raw third-party
    errors may contain internal details. Devs should look at the server logs.
    """
    logger.error(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred. Check server logs for details.",
        },
    )


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    logger.info("DocuSense starting — initialising database schema")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema ready")
    except Exception as exc:
        logger.critical(
            "Database initialisation failed — cannot start: %s", exc, exc_info=True
        )
        sys.exit(1)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}
