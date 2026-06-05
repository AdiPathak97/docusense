from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.base import get_db
from backend.dependencies import get_compiled_graph
from backend.agent.state import AgentState

router = APIRouter(prefix="/api/chat", tags=["chat"])


class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None
    document_ids: list[str] = []   # empty = search all documents


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
    # TODO:
    # 1. Resolve or create ChatSession in DB
    # 2. Build initial AgentState
    # 3. await graph.ainvoke(state)
    # 4. Persist user message + assistant answer to DB
    # 5. Return QueryResponse
    raise NotImplementedError
