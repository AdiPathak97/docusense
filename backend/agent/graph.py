"""
LangGraph StateGraph definition.

Topology (v1): retrieve → grade_docs → generate → END
v2 will add: grade_docs → rewrite_query → retrieve (when all chunks are filtered)

Nodes receive injected dependencies via functools.partial so the graph stays
pure (no global state, no imports of singletons inside node functions).
"""

import functools
from langgraph.graph import StateGraph, END
from backend.agent.state import AgentState
from backend.agent.nodes import retrieve, grade_docs, generate
from backend.services.llm_provider import LLMChatProvider
from backend.services.vector_store import VectorStoreClient


def build_graph(
    chat_provider: LLMChatProvider,
    vector_store: VectorStoreClient,
) -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", functools.partial(retrieve, vector_store=vector_store))
    graph.add_node("grade_docs", functools.partial(grade_docs, chat_provider=chat_provider))
    graph.add_node("generate", functools.partial(generate, chat_provider=chat_provider))

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade_docs")
    graph.add_edge("grade_docs", "generate")
    graph.add_edge("generate", END)

    return graph.compile()
