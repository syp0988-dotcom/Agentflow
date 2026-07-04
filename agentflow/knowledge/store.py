"""High-level KnowledgeStore: ties parsing, embedding, and database together."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentflow.database.sqlite import SQLiteStore
from agentflow.knowledge.embedder import (
    TfidfEmbedder,
    deserialize_vector,
    serialize_vector,
    tokenize,
)
from agentflow.knowledge.parser import parse_document
from agentflow.utils.logging import build_logger

logger = build_logger("knowledge.store")


class KnowledgeStore:
    """Manages document ingestion, vector indexing, and similarity search.

    Usage:
        store = KnowledgeStore()
        doc_id = store.add_document("/path/to/doc.pdf", "doc.pdf")
        results = store.search("user query", top_k=5)
        store.delete_document(doc_id)
    """

    def __init__(self, db: SQLiteStore | None = None) -> None:
        self.db = db or SQLiteStore()
        self.embedder = TfidfEmbedder()
        self._load_embedder_state()

    # -- Document management ---------------------------------------------------

    def add_document(self, file_path: str | Path, filename: str) -> int:
        """Parse a file, chunk it, vectorize chunks, and persist everything.

        Args:
            file_path: Path to the document on disk.
            filename: Original filename (used for display and type detection).

        Returns:
            The document ID.
        """
        path = Path(file_path)
        file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
        file_size = path.stat().st_size

        logger.info("Ingesting document: %s (%d bytes)", filename, file_size)

        # Parse and chunk
        chunks = parse_document(path, file_type)
        logger.info("  → %d chunks extracted", len(chunks))

        # Store document metadata
        doc_id = self.db.add_document(
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            doc_metadata=json.dumps(
                {"chunk_count": len(chunks), "original_path": str(path)}
            ),
        )

        # Chunk, vectorize, and store each piece
        for i, chunk_text in enumerate(chunks):
            tokens = tokenize(chunk_text)
            self.embedder.add_chunk(tokens)
            vector = self.embedder.vectorize(tokens)

            chunk_id = self.db.add_chunk(
                document_id=doc_id,
                content=chunk_text,
                chunk_index=i,
            )
            self.db.add_embedding(chunk_id, serialize_vector(vector))

        # Persist updated embedder state
        self._save_embedder_state()

        logger.info("  → Document #%d indexed successfully", doc_id)
        return doc_id

    def delete_document(self, doc_id: int) -> None:
        """Remove a document and all its chunks/embeddings."""
        # We need to remove chunk tokens from embedder doc_freq.
        # Fetch all chunks first.
        chunks = self.db.get_chunks_by_document(doc_id)
        for chunk in chunks:
            tokens = tokenize(chunk["content"])
            self.embedder.remove_chunk(tokens)

        self.db.delete_document_cascade(doc_id)
        self._save_embedder_state()
        logger.info("Document #%d deleted", doc_id)

    def list_documents(self) -> list[dict[str, Any]]:
        """List all indexed documents with metadata."""
        return self.db.get_all_documents()

    # -- Search ----------------------------------------------------------------

    def search(
        self, query: str, top_k: int = 5, min_score: float = 0.05
    ) -> list[dict[str, Any]]:
        """Search for chunks relevant to the query.

        Args:
            query: Natural language query string.
            top_k: Maximum number of results to return.
            min_score: Minimum similarity score threshold.

        Returns:
            List of dicts with keys: chunk_id, document_id, filename, content, score.
        """
        if self.embedder.num_docs == 0:
            logger.info("No documents indexed; returning empty search results.")
            return []

        query_tokens = tokenize(query)
        query_vec = self.embedder.vectorize(query_tokens)

        # Fetch all stored embeddings
        all_embeddings = self.db.get_all_embeddings_with_chunk()  # list of (chunk_id, embedding_blob, document_id, content)
        candidates: list[tuple[int, np.ndarray]] = []
        for emb in all_embeddings:
            chunk_id = emb["id"]
            vec = deserialize_vector(emb["embedding"])
            candidates.append((chunk_id, vec))

        # Score and rank
        scored = self.embedder.batch_cosine_similarity(query_vec, candidates)

        # Fetch chunk details for top results
        results: list[dict[str, Any]] = []
        for chunk_id, score in scored:
            if score < min_score:
                continue
            if len(results) >= top_k:
                break
            # Get chunk + document info
            chunk_info = self.db.get_chunk_with_document(chunk_id)
            if chunk_info:
                results.append({
                    "chunk_id": chunk_id,
                    "document_id": chunk_info["document_id"],
                    "filename": chunk_info["filename"],
                    "content": chunk_info["content"],
                    "score": round(score, 4),
                })

        return results

    # -- Embedder state persistence --------------------------------------------

    def _load_embedder_state(self) -> None:
        """Restore embedder vocabulary and doc frequencies from the database."""
        state_data = self.db.get_knowledge_meta("embedder_state")
        if state_data:
            try:
                self.embedder.from_dict(json.loads(state_data))
                logger.info(
                    "Loaded embedder state: %d terms, %d docs",
                    len(self.embedder.vocab),
                    self.embedder.num_docs,
                )
            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning("Failed to load embedder state: %s", exc)

    def _save_embedder_state(self) -> None:
        """Persist embedder vocabulary and doc frequencies."""
        state_data = json.dumps(self.embedder.to_dict())
        self.db.set_knowledge_meta("embedder_state", state_data)
        logger.debug(
            "Saved embedder state: %d terms, %d docs",
            len(self.embedder.vocab),
            self.embedder.num_docs,
        )
