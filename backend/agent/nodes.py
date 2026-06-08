"""
LangGraph node functions. Each receives AgentState and returns a partial state dict.
Nodes must not write to DB or external state mid-graph — side effects happen after
the graph returns (see api/chat.py).
"""

import logging

from backend.agent.prompts import (
    GENERATE_SYSTEM,
    GENERATE_USER,
    GRADE_SYSTEM,
    GRADE_USER,
)
from backend.agent.state import AgentState, DocumentChunk
from backend.exceptions import AgentError, LLMError
from backend.services.llm_provider import LLMChatProvider
from backend.services.vector_store import VectorStoreClient
from backend.config import settings

logger = logging.getLogger(__name__)


async def retrieve(state: AgentState, vector_store: VectorStoreClient) -> dict:
    """Query ChromaDB and return top-k chunks."""
    logger.info(
        "retrieve — document_ids=%s top_k=%d",
        state["document_ids"],
        settings.top_k_retrieval,
    )
    # TODO: embed the question via EmbeddingProvider, then query vector_store
    # Return: {"retrieved_chunks": list[DocumentChunk]}
    # VectorStoreError from vector_store.query() will propagate as AgentError
    # via the exception handler in graph.py once implemented.
    raise NotImplementedError


async def grade_docs(state: AgentState, chat_provider: LLMChatProvider) -> dict:
    """
    Score each retrieved chunk for relevance. Filter out chunks below threshold.
    Calls GRADE prompt once per chunk — parallelise with asyncio.gather if latency matters.

    Graceful degradation: if the LLM fails for a single chunk, that chunk is skipped
    (treated as irrelevant) rather than crashing the entire graph. If all chunks fail,
    generate() will return the no-information fallback answer.
    """
    chunks = state["retrieved_chunks"]
    logger.info("grade_docs — chunks_to_grade=%d", len(chunks))
    graded: list[DocumentChunk] = []

    for chunk in chunks:
        try:
            response = await chat_provider.complete(
                system=GRADE_SYSTEM,
                user=GRADE_USER.format(
                    question=state["question"],
                    chunk_content=chunk["content"],
                ),
            )
        except LLMError as exc:
            logger.warning(
                "grade_docs — LLM failed for chunk_id=%s, skipping: %s",
                chunk.get("chunk_id", "unknown"),
                exc,
            )
            continue

        if response.strip().lower() == "yes":
            graded.append(chunk)
        else:
            logger.debug(
                "grade_docs — chunk_id=%s graded irrelevant",
                chunk.get("chunk_id", "unknown"),
            )

    logger.info(
        "grade_docs — passed=%d / %d", len(graded), len(chunks)
    )
    return {"graded_chunks": graded}


async def generate(state: AgentState, chat_provider: LLMChatProvider) -> dict:
    """Synthesise an answer from graded_chunks with inline citations."""
    chunks = state["graded_chunks"]
    logger.info(
        "generate — graded_chunks=%d question_len=%d",
        len(chunks),
        len(state["question"]),
    )

    if not chunks:
        logger.warning(
            "generate — no graded chunks available; returning fallback answer"
        )
        return {
            "answer": "The provided documents do not contain enough information to answer this question.",
            "sources": [],
        }

    formatted_chunks = "\n\n".join(
        f"[{c['document_name']}, p.{c['page_number']}]\n{c['content']}"
        for c in chunks
    )

    try:
        answer = await chat_provider.complete(
            system=GENERATE_SYSTEM,
            user=GENERATE_USER.format(
                question=state["question"],
                chunks=formatted_chunks,
            ),
        )
    except LLMError as exc:
        raise AgentError(
            f"Answer generation failed: {exc}",
            node="generate",
        ) from exc

    logger.info(
        "generate succeeded — answer_chars=%d sources=%d",
        len(answer),
        len(chunks),
    )
    return {"answer": answer, "sources": chunks}
