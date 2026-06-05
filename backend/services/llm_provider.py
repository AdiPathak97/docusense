"""
Provider-agnostic LLM abstraction.

Chat and embedding are deliberately separate protocols because Claude has no
embeddings API. LLM_PROVIDER and EMBEDDING_PROVIDER are configured independently.

Adding a new chat provider: implement LLMChatProvider, register in get_chat_provider().
Adding a new embedding provider: implement EmbeddingProvider, register in get_embedding_provider().
"""

from typing import Protocol, runtime_checkable
from backend.config import Settings


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
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text


# ── Azure OpenAI chat ─────────────────────────────────────────────────────────

class AzureOpenAIChatProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncAzureOpenAI
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment_chat

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content


# ── OpenAI chat ───────────────────────────────────────────────────────────────

class OpenAIChatProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_chat_model

    async def complete(self, system: str, user: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content


# ── Azure OpenAI embeddings ───────────────────────────────────────────────────

class AzureOpenAIEmbeddingProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncAzureOpenAI
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment_embedding

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=self._deployment,
            input=text,
        )
        return response.data[0].embedding


# ── OpenAI embeddings ─────────────────────────────────────────────────────────

class OpenAIEmbeddingProvider:
    def __init__(self, settings: Settings):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model="text-embedding-ada-002",
            input=text,
        )
        return response.data[0].embedding


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
        return MockChatProvider()
    if settings.llm_provider == "claude":
        return ClaudeProvider(settings)
    if settings.llm_provider == "azure_openai":
        return AzureOpenAIChatProvider(settings)
    if settings.llm_provider == "openai":
        return OpenAIChatProvider(settings)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.use_mock_llm:
        return MockEmbeddingProvider()
    if settings.embedding_provider == "azure_openai":
        return AzureOpenAIEmbeddingProvider(settings)
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddingProvider(settings)
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}")
