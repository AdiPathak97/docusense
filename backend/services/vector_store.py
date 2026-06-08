"""
ChromaDB client wrapper.

Collections are namespaced by document_id: "doc_{uuid}".
Multi-tenancy (restricting results to a user's documents) is the responsibility
of the API layer — pass document_ids to query() to filter.
"""

import logging

import chromadb

from backend.config import settings
from backend.exceptions import VectorStoreError

logger = logging.getLogger(__name__)


class VectorStoreClient:
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            logger.debug(
                "Connecting to ChromaDB — host=%s port=%s",
                settings.chroma_host,
                settings.chroma_port,
            )
            try:
                self._client = await chromadb.AsyncHttpClient(
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                )
            except Exception as exc:
                raise VectorStoreError(
                    f"Failed to connect to ChromaDB at "
                    f"{settings.chroma_host}:{settings.chroma_port}: {exc}",
                    operation="_get_client",
                ) from exc
        return self._client

    def _collection_name(self, document_id: str) -> str:
        return f"doc_{document_id}"

    async def upsert_chunks(
        self,
        document_id: str,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        """Upsert embedded chunks into the document's collection."""
        logger.debug(
            "upsert_chunks — document_id=%s count=%d", document_id, len(chunk_ids)
        )
        try:
            client = await self._get_client()
            collection = await client.get_or_create_collection(
                name=self._collection_name(document_id)
            )
            await collection.upsert(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(
                "upsert_chunks succeeded — document_id=%s count=%d",
                document_id,
                len(chunk_ids),
            )
        except VectorStoreError:
            raise  # already wrapped by _get_client; don't double-wrap
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to upsert chunks for document {document_id}: {exc}",
                operation="upsert_chunks",
                document_id=document_id,
            ) from exc

    async def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[dict]:
        """
        Query across one or more document collections.
        Returns top_k results sorted by distance (ascending = most similar first).
        """
        all_results: list[dict] = []
        for doc_id in document_ids:
            client = await self._get_client()

            # A missing collection is expected (ingestion may have failed or not
            # yet completed). Log at WARNING so it is visible but does not block
            # results from other documents in the same query.
            try:
                collection = await client.get_collection(
                    self._collection_name(doc_id)
                )
            except Exception as exc:
                logger.warning(
                    "Could not get collection for doc_id=%s — skipping: %s",
                    doc_id,
                    exc,
                )
                continue

            try:
                result = await collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"],
                )
            except Exception as exc:
                raise VectorStoreError(
                    f"Query failed for document {doc_id}: {exc}",
                    operation="query",
                    document_id=doc_id,
                ) from exc

            ids = result["ids"][0]
            documents = result["documents"][0]
            metadatas = result["metadatas"][0]
            distances = result["distances"][0]
            for chunk_id, text, meta, dist in zip(ids, documents, metadatas, distances):
                all_results.append({
                    "id": chunk_id,
                    "text": text,
                    "metadata": meta,
                    "distance": dist,
                })

        all_results.sort(key=lambda r: r["distance"])
        return all_results[:top_k]

    async def delete_document(self, document_id: str) -> None:
        """Drop the entire collection for a document."""
        logger.info("delete_document — document_id=%s", document_id)
        try:
            client = await self._get_client()
            await client.delete_collection(self._collection_name(document_id))
            logger.debug("delete_document succeeded — document_id=%s", document_id)
        except VectorStoreError:
            raise
        except Exception as exc:
            raise VectorStoreError(
                f"Failed to delete collection for document {document_id}: {exc}",
                operation="delete_document",
                document_id=document_id,
            ) from exc
