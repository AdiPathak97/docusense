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
        self._client = None

    async def _get_client(self):
        if self._client is None:
            self._client = await chromadb.AsyncHttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
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
            try:
                collection = await client.get_collection(self._collection_name(doc_id))
            except Exception:
                continue
            result = await collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
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
        client = await self._get_client()
        await client.delete_collection(self._collection_name(document_id))
