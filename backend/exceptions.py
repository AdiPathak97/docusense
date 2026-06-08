"""
Custom exception hierarchy for DocuSense.

All application exceptions inherit from DocuSenseError so the global FastAPI
exception handler can catch them in one place and return structured JSON responses
without leaking raw third-party tracebacks to the client.

Raise the most specific subclass possible so callers can handle different failure
modes selectively if needed.
"""


class DocuSenseError(Exception):
    """Base class for all application-level errors.

    str(exc) returns the human-readable message passed at construction — safe to
    surface in HTTP responses. Never put API keys, raw SQL, or internal paths in
    the message.
    """


class IngestionError(DocuSenseError):
    """Raised when document parsing, chunking, or embedding fails.

    Covers: PDF/DOCX/TXT parse errors, tiktoken chunking failures, and embedding
    API calls that fail during the ingestion pipeline.
    """

    def __init__(self, message: str, *, document_id: str = "") -> None:
        super().__init__(message)
        self.document_id = document_id


class VectorStoreError(DocuSenseError):
    """Raised when ChromaDB operations fail.

    Covers: connection failures, upsert errors, query errors, and delete errors.
    """

    def __init__(
        self, message: str, *, operation: str = "", document_id: str = ""
    ) -> None:
        super().__init__(message)
        self.operation = operation
        self.document_id = document_id


class LLMError(DocuSenseError):
    """Raised when an LLM or embedding provider API call fails.

    Covers: authentication errors, rate limits, timeouts, malformed responses,
    and unknown provider configuration.
    """

    def __init__(
        self, message: str, *, provider: str = "", operation: str = ""
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.operation = operation


class AgentError(DocuSenseError):
    """Raised when a LangGraph node fails in a way that cannot be recovered gracefully.

    grade_docs uses graceful degradation (skip the chunk) so it does not raise
    AgentError. generate raises AgentError because there is no safe silent fallback
    for a generation failure.
    """

    def __init__(self, message: str, *, node: str = "") -> None:
        super().__init__(message)
        self.node = node
