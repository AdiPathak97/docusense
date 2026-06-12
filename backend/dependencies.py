"""
FastAPI dependency injection.
All service singletons are created once at startup and injected via Depends().
"""

import logging
from functools import lru_cache

from backend.config import settings
from backend.agent.graph import build_graph
from backend.exceptions import LLMError
from backend.services.llm_provider import (
    EmbeddingProvider,
    LLMChatProvider,
    get_chat_provider,
    get_embedding_provider,
)
from backend.services.vector_store import VectorStoreClient

logger = logging.getLogger(__name__)


@lru_cache
def get_settings():
    return settings


@lru_cache
def get_vector_store() -> VectorStoreClient:
    return VectorStoreClient()


@lru_cache
def get_chat_provider_dep() -> LLMChatProvider:
    try:
        return get_chat_provider(settings)
    except LLMError as exc:
        logger.critical("Failed to initialise chat provider: %s", exc)
        raise


@lru_cache
def get_embedding_provider_dep() -> EmbeddingProvider:
    try:
        return get_embedding_provider(settings)
    except LLMError as exc:
        logger.critical("Failed to initialise embedding provider: %s", exc)
        raise


@lru_cache
def get_compiled_graph():
    logger.info(
        "Building LangGraph — chat_provider=%s embedding_provider=%s vector_store=%s",
        type(get_chat_provider_dep()).__name__,
        type(get_embedding_provider_dep()).__name__,
        type(get_vector_store()).__name__,
    )
    return build_graph(
        chat_provider=get_chat_provider_dep(),
        vector_store=get_vector_store(),
        embedding_provider=get_embedding_provider_dep(),
    )
