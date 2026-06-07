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
    if content_type == "application/pdf":
        import pypdf
        pages = []
        reader = pypdf.PdfReader(str(file_path))
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page_number": i, "text": text})
        return pages

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(str(file_path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"page_number": 1, "text": text}]

    # text/plain
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return [{"page_number": 1, "text": text}]


def chunk_pages(pages: list[dict]) -> list[dict]:
    """
    Split pages into chunks. Returns list of {chunk_index, page_number, text}.
    Uses RecursiveCharacterTextSplitter with tiktoken encoder.
    """
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = []
    chunk_index = 0
    for page in pages:
        splits = splitter.split_text(page["text"])
        for split in splits:
            chunks.append({
                "chunk_index": chunk_index,
                "page_number": page["page_number"],
                "text": split,
            })
            chunk_index += 1
    return chunks


async def ingest(
    document_id: str,
    document_name: str,
    file_path: Path,
    content_type: str,
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStoreClient,
) -> list[dict]:
    """
    Full pipeline. Returns list of ingested chunks (id, chunk_index, page_number).
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
    return [
        {"id": cid, "chunk_index": c["chunk_index"], "page_number": c["page_number"]}
        for cid, c in zip(chunk_ids, chunks)
    ]
