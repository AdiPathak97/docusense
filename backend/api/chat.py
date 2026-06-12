import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agent.state import AgentState
from backend.db.base import get_db
from backend.dependencies import get_compiled_graph
from backend.models.document import Document, ProcessingStatus
from backend.models.session import ChatSession, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None
    document_ids: list[str] = []   # empty = search all complete documents


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[dict]


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    graph=Depends(get_compiled_graph),
):
    # 1. Resolve or create ChatSession
    if request.session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == request.session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            logger.warning(
                "session_id=%s not found — creating new session", request.session_id
            )
            session = ChatSession(id=request.session_id)
            db.add(session)
            await db.flush()
    else:
        session = ChatSession()
        db.add(session)
        await db.flush()

    session_id = session.id
    logger.info(
        "chat query — session_id=%s question_len=%d", session_id, len(request.question)
    )

    # 2. Resolve document_ids — empty means search all ingested documents
    document_ids = request.document_ids
    if not document_ids:
        result = await db.execute(
            select(Document.id).where(Document.status == ProcessingStatus.complete)
        )
        document_ids = list(result.scalars().all())
        logger.debug(
            "No document_ids specified — resolved to all complete docs: count=%d",
            len(document_ids),
        )

    if not document_ids:
        # No documents have been ingested yet; skip graph invocation
        await db.commit()
        return QueryResponse(
            answer="No documents have been uploaded yet. Please upload a document first.",
            session_id=session_id,
            sources=[],
        )

    # 3. Build initial AgentState and invoke the LangGraph agent
    initial_state: AgentState = {
        "question": request.question,
        "session_id": session_id,
        "document_ids": document_ids,
        "retrieved_chunks": [],
        "graded_chunks": [],
        "rewrite_count": 0,
        "answer": "",
        "sources": [],
    }

    result_state = await graph.ainvoke(initial_state)

    answer: str = result_state["answer"]
    sources: list[dict] = [dict(chunk) for chunk in result_state["sources"]]

    logger.info(
        "chat query complete — session_id=%s answer_chars=%d sources=%d",
        session_id,
        len(answer),
        len(sources),
    )

    # 4. Persist user message and assistant answer
    db.add(Message(session_id=session_id, role="user", content=request.question))
    db.add(Message(session_id=session_id, role="assistant", content=answer))
    await db.commit()

    # 5. Return response
    return QueryResponse(
        answer=answer,
        session_id=session_id,
        sources=sources,
    )
