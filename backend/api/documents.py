import logging
import shutil
import tempfile
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import AsyncSessionLocal, get_db
from backend.dependencies import get_embedding_provider_dep, get_vector_store
from backend.exceptions import DocuSenseError, VectorStoreError
from backend.models.document import Chunk, Document, ProcessingStatus
from backend.services.ingestion import ingest

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


async def _run_ingestion(
    document_id: str,
    document_name: str,
    tmp_path: Path,
    content_type: str,
    embedding_provider,
    vector_store,
) -> None:
    """Background task: ingest the file, persist chunk rows, update document status."""
    async with AsyncSessionLocal() as db:
        try:
            ingested = await ingest(
                document_id=document_id,
                document_name=document_name,
                file_path=tmp_path,
                content_type=content_type,
                embedding_provider=embedding_provider,
                vector_store=vector_store,
            )

            for c in ingested:
                db.add(Chunk(
                    id=c["id"],
                    document_id=document_id,
                    chunk_index=c["chunk_index"],
                    page_number=c["page_number"],
                ))

            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one()
            doc.status = ProcessingStatus.complete
            doc.chunk_count = len(ingested)
            await db.commit()
        except DocuSenseError as exc:
            # Typed error — the message is already self-describing (e.g.
            # "OpenAI embedding request failed: Connection error."). Log at
            # ERROR without traceback to keep logs readable; the root cause
            # is embedded in the message via `raise X from exc`.
            logger.error(
                "Ingestion failed [%s] — document_id=%s name=%s: %s",
                type(exc).__name__,
                document_id,
                document_name,
                exc,
            )
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = ProcessingStatus.failed
                await db.commit()
        except Exception:
            # Unexpected error — log with full traceback because we don't know
            # what went wrong and need the stack to diagnose it.
            logger.exception(
                "Unexpected ingestion error — document_id=%s name=%s",
                document_id,
                document_name,
            )
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = ProcessingStatus.failed
                await db.commit()
        finally:
            tmp_path.unlink(missing_ok=True)


@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
    embedding_provider=Depends(get_embedding_provider_dep),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    # Write upload to a temp file that outlives the request
    suffix = Path(file.filename).suffix if file.filename else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        shutil.copyfileobj(file.file, tmp)
    finally:
        tmp.close()

    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        name=file.filename or "upload",
        content_type=file.content_type,
        status=ProcessingStatus.processing,
    )
    db.add(doc)
    await db.commit()
    logger.info(
        "Document accepted — id=%s name=%s content_type=%s",
        doc_id,
        doc.name,
        file.content_type,
    )

    background_tasks.add_task(
        _run_ingestion,
        document_id=doc_id,
        document_name=file.filename or "upload",
        tmp_path=Path(tmp.name),
        content_type=file.content_type,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    return {"id": doc_id, "name": doc.name, "status": doc.status}


@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "content_type": d.content_type,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    await db.commit()

    # Vector store delete is best-effort: the collection may not exist if ingestion
    # never completed. Always return 204 regardless.
    try:
        await vector_store.delete_document(document_id)
    except VectorStoreError as exc:
        logger.warning(
            "Vector store delete skipped — document_id=%s: %s", document_id, exc
        )
    except Exception as exc:
        logger.warning(
            "Unexpected error deleting vector store collection — document_id=%s: %s",
            document_id,
            exc,
        )
