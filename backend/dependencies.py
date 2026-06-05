"""
FastAPI dependency injection.
All service singletons are created once at startup and injected via Depends().
"""

from functools import lru_cache
from backend.config import settings
from backend.services.llm_provider import get_chat_provider, get_embedding_provider, LLMChatProvider, EmbeddingProvider
from backend.services.vector_store import VectorStoreClient
from backend.agent.graph import build_graph


@lru_cache
def get_settings():
    return settings


@lru_cache
def get_vector_store() -> VectorStoreClient:
    return VectorStoreClient()


@lru_cache
def get_chat_provider_dep() -> LLMChatProvider:
    return get_chat_provider(settings)


@lru_cache
def get_embedding_provider_dep() -> EmbeddingProvider:
    return get_embedding_provider(settings)


@lru_cache
def get_compiled_graph():
    return build_graph(
        chat_provider=get_chat_provider_dep(),
        vector_store=get_vector_store(),
    )
