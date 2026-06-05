"""
Document ingestion pipeline: parse → chunk → embed → upsert.

Chunk size (500 tokens, overlap 50) is set in config.
If you change it, increment EMBEDDING_VERSION and re-embed all existing documents.
"""

import uuid
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.services.llm_provider import EmbeddingProvider
from backend.services.vector_store import VectorStoreClient

CHUNK_SIZE = 500    # tokens
CHUNK_OVERLAP = 50  # tokens
EMBEDDING_VERSION = 1


def parse_document(file_path: Path, content_type: str) -> list[dict]:
    """
    Parse uploaded file into a list of {page_number, text} dicts.
    Supported: application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, text/plain
    """
    # TODO: implement pypdf / python-docx / plain text parsing
    raise NotImplementedError


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split pages into chunks. Returns list of {chunk_index, page_number, text}.
    Uses RecursiveCharacterTextSplitter with tiktoken encoder.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    # TODO: split each page's text, track page_number per chunk
    raise NotImplementedError


async def ingest(
    document_id: str,
    document_name: str,
    file_path: Path,
    content_type: str,
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStoreClient,
) -> int:
    """
    Full pipeline. Returns number of chunks ingested.
    Called from POST /api/documents/upload after DB record is created.
    """
    pages = parse_document(file_path, content_type)
    chunks = chunk_pages(pages)

    chunk_ids, embeddings, documents, metadatas = [], [], [], []
    for chunk in chunks:
        chunk_id = str(uuid.uuid4())
        embedding = await embedding_provider.embed(chunk["text"])
        chunk_ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(chunk["text"])
        metadatas.append({
            "document_id": document_id,
            "document_name": document_name,
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "embedding_version": EMBEDDING_VERSION,
        })

    await vector_store.upsert_chunks(document_id, chunk_ids, embeddings, documents, metadatas)
    return len(chunks)
