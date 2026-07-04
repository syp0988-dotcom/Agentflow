"""SQLite-backed persistence for chat history and knowledge base."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from agentflow.config.settings import settings


class SQLiteStore:
    """Simple SQLite-backed persistence for chat/history and knowledge base data."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")

            connection.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    doc_metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id INTEGER NOT NULL UNIQUE,
                    embedding BLOB NOT NULL,
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
                )
            """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            connection.commit()

    # -- Chat history ----------------------------------------------------------

    def add_message(self, role: str, content: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT INTO chats(role, content, created_at) VALUES (?, ?, datetime('now'))",
                (role, content),
            )
            connection.commit()

    def list_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT role, content, created_at FROM chats ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            {"role": role, "content": content, "created_at": created_at}
            for role, content, created_at in rows
        ]

    # -- Documents -------------------------------------------------------------

    def add_document(
        self, filename: str, file_type: str, file_size: int, doc_metadata: str = "{}"
    ) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO documents(filename, file_type, file_size, doc_metadata) VALUES (?, ?, ?, ?)",
                (filename, file_type, file_size, doc_metadata),
            )
            connection.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_all_documents(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT id, filename, file_type, file_size, doc_metadata, created_at "
                "FROM documents ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "filename": row[1],
                "file_type": row[2],
                "file_size": row[3],
                "doc_metadata": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def delete_document_cascade(self, doc_id: int) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            connection.commit()

    # -- Chunks ----------------------------------------------------------------

    def add_chunk(self, document_id: int, content: str, chunk_index: int) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "INSERT INTO chunks(document_id, content, chunk_index) VALUES (?, ?, ?)",
                (document_id, content, chunk_index),
            )
            connection.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_chunks_by_document(self, doc_id: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT id, content, chunk_index FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (doc_id,),
            )
            rows = cursor.fetchall()
        return [
            {"id": row[0], "content": row[1], "chunk_index": row[2]} for row in rows
        ]

    def get_chunk_with_document(self, chunk_id: int) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT c.id, c.document_id, c.content, d.filename "
                "FROM chunks c JOIN documents d ON c.document_id = d.id "
                "WHERE c.id = ?",
                (chunk_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "document_id": row[1],
            "content": row[2],
            "filename": row[3],
        }

    # -- Embeddings ------------------------------------------------------------

    def add_embedding(self, chunk_id: int, embedding_blob: bytes) -> int:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "INSERT OR REPLACE INTO embeddings(chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, embedding_blob),
            )
            connection.commit()
            return cursor.lastrowid  # type: ignore[return-value]

    def get_all_embeddings_with_chunk(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT e.id, e.chunk_id, e.embedding, c.document_id, c.content "
                "FROM embeddings e "
                "JOIN chunks c ON e.chunk_id = c.id"
            )
            rows = cursor.fetchall()
        return [
            {
                "id": row[1],  # chunk_id
                "chunk_id": row[1],
                "embedding": row[2],
                "document_id": row[3],
                "content": row[4],
            }
            for row in rows
        ]

    # -- Knowledge metadata ----------------------------------------------------

    def get_knowledge_meta(self, key: str) -> str | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.execute(
                "SELECT value FROM knowledge_meta WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def set_knowledge_meta(self, key: str, value: str) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO knowledge_meta(key, value) VALUES (?, ?)",
                (key, value),
            )
            connection.commit()
