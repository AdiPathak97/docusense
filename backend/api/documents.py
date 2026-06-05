from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.base import get_db
from backend.dependencies import get_vector_store, get_embedding_provider_dep
from backend.services.ingestion import ingest
from backend.models.document import Document, ProcessingStatus
import tempfile, shutil
from pathlib import Path

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider_dep),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    # TODO: save file to temp, create DB record, kick off ingestion as background task
    raise NotImplementedError


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    # TODO: return all documents with status
    raise NotImplementedError


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
):
    # TODO: delete from DB + ChromaDB collection
    raise NotImplementedError
