"""
Provider-agnostic LLM abstraction.

Chat and embedding are deliberately separate protocols because Claude has no
embeddings API. LLM_PROVIDER and EMBEDDING_PROVIDER are configured independently.

Adding a new chat provider: implement LLMChatProvider, register in get_chat_provider().
Adding a new embedding provider: implement EmbeddingProvider, register in get_embedding_provider().
"""

import logging
from typing import Protocol, runtime_checkable

from backend.config import Settings
from backend.exceptions import LLMError

logger = logging.getLogger(__name__)


# ── Protocols ─────────────────────────────────────────────────────────────────

@runtime_checkable
class LLMChatProvider(Protocol):
    async def complete(self, system: str, user: str) -> str:
        """Send a system + user turn, return the assistant's text response."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for a single text string."""
        ...


# ── Claude ────────────────────────────────────────────────────────────────────

class ClaudeProvider:
    """Primary chat provider. Requires ANTHROPIC_API_KEY."""

    def __init__(self, settings: Settings):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model

    async def complete(self, system: str, user: str) -> str:
        logger.debug("LLM complete — provider=claude model=%s", self._model)
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            result = message.content[0].text
            logger.debug("LLM complete ok — provider=claude chars=%d", len(result))
            return result
        except Exception as exc:
            logger.error("LLM complete failed — provider=claude: %s", exc)
            raise LLMError(
                f"Claude API request failed: {exc}",
                provider="claude",
                operation="complete",
            ) from exc


# ── Azure OpenAI chat ─────────────────────────────────────────────────────────

def _is_foundry_endpoint(endpoint: str) -> bool:
    """
    Foundry resources expose /openai/v1/ (serverless, OpenAI-compatible).
    Classic Azure OpenAI resources expose /openai/ (deployment-based, api-version param).
    Detect by presence of /openai/v1 in the URL so both endpoint styles work
    without extra config.
    """
    return "/openai/v1" in endpoint.rstrip("/")


def _make_azure_client(settings: Settings):
    """
    Return the right async OpenAI client for the configured endpoint.

    Foundry /openai/v1 endpoint → AsyncOpenAI(base_url=...) — no api-version.
    Classic /openai/ endpoint   → AsyncAzureOpenAI(azure_endpoint=...) — api-version required.
    """
    endpoint = settings.azure_openai_endpoint.rstrip("/")
    if _is_foundry_endpoint(endpoint):
        from openai import AsyncOpenAI
        logger.debug("Azure client mode: Foundry /openai/v1 (standard OpenAI-compatible)")
        return AsyncOpenAI(
            base_url=endpoint + "/",
            api_key=settings.azure_openai_api_key,
        )
    else:
        from openai import AsyncAzureOpenAI
        logger.debug("Azure client mode: classic Azure OpenAI (deployment-based)")
        return AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )


class AzureOpenAIChatProvider:
    def __init__(self, settings: Settings):
        self._client = _make_azure_client(settings)
        self._deployment = settings.azure_openai_deployment_chat

    async def complete(self, system: str, user: str) -> str:
        logger.debug("LLM complete — provider=azure_openai deployment=%s", self._deployment)
        try:
            response = await self._client.chat.completions.create(
                model=self._deployment,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            result = response.choices[0].message.content
            logger.debug("LLM complete ok — provider=azure_openai chars=%d", len(result))
            return result
        except Exception as exc:
            logger.error("LLM complete failed — provider=azure_openai: %s", exc)
            raise LLMError(
                f"Azure OpenAI chat request failed: {exc}",
                provider="azure_openai",
                operation="complete",
            ) from exc


# ── OpenAI chat ───────────────────────────────────────────────────────────────

class OpenAIChatProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    async def complete(self, system: str, user: str) -> str:
        logger.debug("LLM complete — provider=openai model=%s", self._model)
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            result = response.choices[0].message.content
            logger.debug("LLM complete ok — provider=openai chars=%d", len(result))
            return result
        except Exception as exc:
            logger.error("LLM complete failed — provider=openai: %s", exc)
            raise LLMError(
                f"OpenAI chat request failed: {exc}",
                provider="openai",
                operation="complete",
            ) from exc


# ── Azure OpenAI embeddings ───────────────────────────────────────────────────

class AzureOpenAIEmbeddingProvider:
    def __init__(self, settings: Settings):
        self._client = _make_azure_client(settings)
        self._deployment = settings.azure_openai_deployment_embedding

    async def embed(self, text: str) -> list[float]:
        logger.debug("Embedding — provider=azure_openai deployment=%s", self._deployment)
        try:
            response = await self._client.embeddings.create(
                model=self._deployment,
                input=text,
            )
            result = response.data[0].embedding
            logger.debug("Embedding ok — provider=azure_openai dims=%d", len(result))
            return result
        except Exception as exc:
            logger.error("Embedding failed — provider=azure_openai: %s", exc)
            raise LLMError(
                f"Azure OpenAI embedding request failed: {exc}",
                provider="azure_openai",
                operation="embed",
            ) from exc


# ── OpenAI embeddings ─────────────────────────────────────────────────────────

class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(self, text: str) -> list[float]:
        logger.debug("Embedding — provider=openai model=text-embedding-ada-002")
        try:
            response = await self._client.embeddings.create(
                model="text-embedding-ada-002",
                input=text,
            )
            result = response.data[0].embedding
            logger.debug("Embedding ok — provider=openai dims=%d", len(result))
            return result
        except Exception as exc:
            logger.error("Embedding failed — provider=openai: %s", exc)
            raise LLMError(
                f"OpenAI embedding request failed: {exc}",
                provider="openai",
                operation="embed",
            ) from exc


# ── Mock (USE_MOCK_LLM=true) ──────────────────────────────────────────────────

class MockChatProvider:
    """Returns canned responses. No API key required. For local dev only."""

    async def complete(self, system: str, user: str) -> str:
        if "yes" in system.lower() or "no" in system.lower():
            return "yes"
        return "This is a mock answer. Set USE_MOCK_LLM=false to use a real provider."


class MockEmbeddingProvider:
    async def embed(self, text: str) -> list[float]:
        return [0.0] * 1536


# ── Factories ─────────────────────────────────────────────────────────────────

def get_chat_provider(settings: Settings) -> LLMChatProvider:
    if settings.use_mock_llm:
        logger.warning(
            "Mock LLM active (USE_MOCK_LLM=true) — responses are not real"
        )
        return MockChatProvider()
    logger.info(
        "Initialising chat provider — llm_provider=%s", settings.llm_provider
    )
    if settings.llm_provider == "claude":
        return ClaudeProvider(settings)
    if settings.llm_provider == "azure_openai":
        return AzureOpenAIChatProvider(settings)
    if settings.llm_provider == "openai":
        return OpenAIChatProvider(settings)
    raise LLMError(
        f"Unknown LLM_PROVIDER: '{settings.llm_provider}'. "
        f"Valid values: claude, azure_openai, openai.",
        provider=settings.llm_provider,
        operation="init",
    )


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.use_mock_llm:
        logger.warning(
            "Mock embedding provider active (USE_MOCK_LLM=true) — embeddings are not real"
        )
        return MockEmbeddingProvider()
    logger.info(
        "Initialising embedding provider — embedding_provider=%s",
        settings.embedding_provider,
    )
    if settings.embedding_provider == "azure_openai":
        return AzureOpenAIEmbeddingProvider(settings)
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    raise LLMError(
        f"Unknown EMBEDDING_PROVIDER: '{settings.embedding_provider}'. "
        f"Valid values: azure_openai, openai.",
        provider=settings.embedding_provider,
        operation="init",
    )
