"""
Chroma-backed storage for proposal chunks.

We always compute embeddings ourselves via EmbeddingProvider and pass them
explicitly to Chroma (rather than relying on Chroma's internal auto-embed
hook). This keeps embedding failures fully under our control and makes the
store trivially testable with a hash-based embedding provider.
"""
from __future__ import annotations

from typing import List, Optional

from app.retrieval.embeddings import EmbeddingProvider
from app.schemas.evidence import DocumentChunk, EvidenceSnippet
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("chroma_store")


class RetrievalError(Exception):
    """Raised on unrecoverable retrieval/storage failures."""


class ChromaStore:
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        in_memory: bool = False,
    ):
        settings = get_settings()
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedder = embedding_provider or EmbeddingProvider()
        self._client = None
        self._collection = None
        self._in_memory = in_memory

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb

            if self._in_memory:
                self._client = chromadb.EphemeralClient()
            else:
                self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Could not initialize the Chroma vector store: {exc}") from exc
        return self._collection

    def reset_project(self) -> None:
        """Clear all stored chunks (used when starting a new analysis)."""
        try:
            collection = self._ensure_collection()
            existing = collection.get(include=[])
            ids = existing.get("ids", [])
            if ids:
                collection.delete(ids=ids)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fully reset the vector store: %s", exc)

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Embed and insert chunks. Returns the number of chunks stored."""
        if not chunks:
            return 0
        collection = self._ensure_collection()
        texts = [c.text for c in chunks]
        try:
            embeddings = self.embedder.embed(texts)
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Embedding generation failed: {exc}") from exc

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "vendor": c.vendor,
                "document": c.document,
                "page_number": c.page_number if c.page_number is not None else -1,
                "section": c.section or "",
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]
        try:
            collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Failed to store chunks in Chroma: {exc}") from exc
        return len(chunks)

    def count(self) -> int:
        try:
            return self._ensure_collection().count()
        except Exception:  # noqa: BLE001
            return 0

    def query(
        self,
        query_text: str,
        top_k: int = 4,
        vendor_filter: Optional[str] = None,
    ) -> List[EvidenceSnippet]:
        """Return the top_k most relevant chunks as EvidenceSnippet objects."""
        collection = self._ensure_collection()
        if collection.count() == 0:
            return []

        try:
            query_embedding = self.embedder.embed([query_text])[0]
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Embedding the query failed: {exc}") from exc

        where = {"vendor": vendor_filter} if vendor_filter else None
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, max(1, collection.count())),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001
            raise RetrievalError(f"Chroma query failed: {exc}") from exc

        snippets: List[EvidenceSnippet] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc_text, meta, dist in zip(docs, metas, distances):
            page = meta.get("page_number")
            snippets.append(
                EvidenceSnippet(
                    vendor=meta.get("vendor", "Unknown"),
                    document=meta.get("document"),
                    page_number=page if isinstance(page, int) and page >= 0 else None,
                    section=meta.get("section") or None,
                    source_text=doc_text,
                    evidence_type="retrieval",
                    relevance_score=round(1.0 - dist, 4) if isinstance(dist, (int, float)) else None,
                )
            )
        return snippets
