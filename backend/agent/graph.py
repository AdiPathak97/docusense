"""
LangGraph StateGraph definition.

Topology (v2):
    retrieve → grade_docs → [router] → generate → END
                                ↓  (graded_chunks empty AND rewrite_count < MAX_REWRITES)
                           rewrite_query → retrieve

MAX_REWRITES caps the loop at 2 attempts (configurable here).
If all rewrites still yield no graded chunks, generate() returns a graceful fallback.
"""

import functools
from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState
from backend.agent.nodes import generate, grade_docs, retrieve, rewrite_query
from backend.services.llm_provider import EmbeddingProvider, LLMChatProvider
from backend.services.vector_store import VectorStoreClient

MAX_REWRITES = 2


def _route_after_grade(state: AgentState) -> str:
    """
    After grade_docs: if no chunks passed grading AND we haven't hit the rewrite
    limit, send to rewrite_query. Otherwise proceed to generate (which handles
    the empty-context case gracefully).
    """
    if not state["graded_chunks"] and state["rewrite_count"] < MAX_REWRITES:
        return "rewrite_query"
    return "generate"


def build_graph(
    chat_provider: LLMChatProvider,
    vector_store: VectorStoreClient,
    embedding_provider: EmbeddingProvider,
) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node(
        "retrieve",
        functools.partial(
            retrieve,
            vector_store=vector_store,
            embedding_provider=embedding_provider,
        ),
    )
    graph.add_node(
        "grade_docs",
        functools.partial(grade_docs, chat_provider=chat_provider),
    )
    graph.add_node(
        "generate",
        functools.partial(generate, chat_provider=chat_provider),
    )
    graph.add_node(
        "rewrite_query",
        functools.partial(rewrite_query, chat_provider=chat_provider),
    )

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade_docs")
    graph.add_conditional_edges(
        "grade_docs",
        _route_after_grade,
        {"rewrite_query": "rewrite_query", "generate": "generate"},
    )
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", END)

    return graph.compile()
