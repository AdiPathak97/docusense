from typing import TypedDict


class DocumentChunk(TypedDict):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    relevance_score: float | None  # populated by grade_docs node


class AgentState(TypedDict):
    # Set before graph invocation
    question: str
    session_id: str
    document_ids: list[str]          # restrict search to these docs; empty = all

    # Populated by retrieve node
    retrieved_chunks: list[DocumentChunk]

    # Populated by grade_docs node (filtered subset of retrieved_chunks)
    graded_chunks: list[DocumentChunk]

    # Populated by generate node
    answer: str
    sources: list[DocumentChunk]     # chunks cited in the final answer
