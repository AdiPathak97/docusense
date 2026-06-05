"""
ChromaDB client wrapper.

Collections are namespaced by document_id: "doc_{uuid}".
Multi-tenancy (restricting results to a user's documents) is the responsibility
of the API layer — pass document_ids to query() to filter.
"""

import chromadb
from backend.config import settings


class VectorStoreClient:
    def __init__(self):
        self._client = chromadb.AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
        )

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
        collection = await self._client.get_or_create_collection(
            name=self._collection_name(document_id)
        )
        await collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    async def query(
        self,
        query_embedding: list[float],
        document_ids: list[str],
        top_k: int,
    ) -> list[dict]:
        """
        Query across one or more document collections.
        Returns merged, unsorted results — caller ranks by distance.
        """
        # TODO: query each collection, merge results, sort by distance, return top_k
        raise NotImplementedError

    async def delete_document(self, document_id: str) -> None:
        """Drop the entire collection for a document."""
        await self._client.delete_collection(self._collection_name(document_id))
