"""
LangGraph node functions. Each receives AgentState and returns a partial state dict.
Nodes must not write to DB or external state mid-graph — side effects happen after
the graph returns (see api/chat.py).
"""

from backend.agent.state import AgentState, DocumentChunk
from backend.agent.prompts import (
    GRADE_SYSTEM, GRADE_USER,
    GENERATE_SYSTEM, GENERATE_USER,
)
from backend.services.llm_provider import LLMChatProvider
from backend.services.vector_store import VectorStoreClient
from backend.config import settings


async def retrieve(state: AgentState, vector_store: VectorStoreClient) -> dict:
    """Query ChromaDB and return top-k chunks."""
    # TODO: embed the question via EmbeddingProvider, then query vector_store
    # Return: {"retrieved_chunks": list[DocumentChunk]}
    raise NotImplementedError


async def grade_docs(state: AgentState, chat_provider: LLMChatProvider) -> dict:
    """
    Score each retrieved chunk for relevance. Filter out chunks below threshold.
    Calls GRADE prompt once per chunk — parallelise with asyncio.gather if latency matters.
    """
    graded: list[DocumentChunk] = []

    for chunk in state["retrieved_chunks"]:
        response = await chat_provider.complete(
            system=GRADE_SYSTEM,
            user=GRADE_USER.format(
                question=state["question"],
                chunk_content=chunk["content"],
            ),
        )
        if response.strip().lower() == "yes":
            graded.append(chunk)

    return {"graded_chunks": graded}


async def generate(state: AgentState, chat_provider: LLMChatProvider) -> dict:
    """Synthesise an answer from graded_chunks with inline citations."""
    chunks = state["graded_chunks"]

    if not chunks:
        return {
            "answer": "The provided documents do not contain enough information to answer this question.",
            "sources": [],
        }

    formatted_chunks = "\n\n".join(
        f"[{c['document_name']}, p.{c['page_number']}]\n{c['content']}"
        for c in chunks
    )

    answer = await chat_provider.complete(
        system=GENERATE_SYSTEM,
        user=GENERATE_USER.format(
            question=state["question"],
            chunks=formatted_chunks,
        ),
    )

    return {"answer": answer, "sources": chunks}
