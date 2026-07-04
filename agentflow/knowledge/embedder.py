"""TF-IDF vectorizer and cosine similarity search for document chunks.

This module implements a lightweight, dependency-minimal embedding approach:
- Tokenization at character level for Chinese, word level for English
- TF-IDF weighted vector representation
- Cosine similarity for ranking

For semantic search (sentence-transformers), set settings.knowledge_embedder = "semantic"
and install: pip install sentence-transformers
"""

from __future__ import annotations

import math
import re
import struct
from collections import Counter
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Regex to split Chinese characters from English words/tokens.
# Each Chinese character becomes its own token; English words are split on
# whitespace/punctuation.
_CHINESE_RE = re.compile(r"[一-鿿㐀-䶿豈-﫿]")
_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]+|[^\s]")


def tokenize(text: str) -> list[str]:
    """Tokenize mixed Chinese/English text into tokens.

    Chinese characters are treated as unigram tokens.
    English words are lowercased and split on whitespace/punctuation.
    """
    tokens: list[str] = []
    for match in _TOKEN_RE.finditer(text.lower()):
        tok = match.group()
        # Split Chinese characters into individual tokens
        if _CHINESE_RE.match(tok):
            tokens.extend(list(tok))
        else:
            tokens.append(tok)
    return tokens


# ---------------------------------------------------------------------------
# TF-IDF Embedder
# ---------------------------------------------------------------------------


class TfidfEmbedder:
    """Lightweight TF-IDF vectorizer that stores vocabulary in memory.

    State can be serialized/deserialized via ``to_dict`` / ``from_dict`` for
    persistence in the database alongside document vectors.
    """

    def __init__(self) -> None:
        # term -> index in the vector
        self.vocab: dict[str, int] = {}
        # term_index -> number of documents containing that term
        self.doc_freq: dict[int, int] = {}
        self.num_docs: int = 0

    # -- Vocabulary maintenance ------------------------------------------------

    def add_chunk(self, tokens: list[str]) -> None:
        """Update vocabulary and document frequency with a new chunk's tokens."""
        self.num_docs += 1
        seen: set[str] = set()
        for tok in tokens:
            if tok not in self.vocab:
                self.vocab[tok] = len(self.vocab)
            idx = self.vocab[tok]
            if tok not in seen:
                self.doc_freq[idx] = self.doc_freq.get(idx, 0) + 1
                seen.add(tok)

    def remove_chunk(self, tokens: list[str]) -> None:
        """Decrement document frequency (call when a chunk is deleted)."""
        seen: set[str] = set()
        for tok in tokens:
            idx = self.vocab.get(tok)
            if idx is not None and tok not in seen:
                self.doc_freq[idx] = max(0, self.doc_freq.get(idx, 0) - 1)
                seen.add(tok)
                if self.doc_freq[idx] == 0:
                    self.doc_freq.pop(idx, None)
            if tok not in seen:
                seen.add(tok)
        self.num_docs = max(0, self.num_docs - 1)

    # -- Vectorization ---------------------------------------------------------

    def vectorize(self, tokens: list[str]) -> np.ndarray:
        """Compute TF-IDF vector for a token list.

        Returns a 1-D numpy array of shape (len(vocab),).
        """
        if not self.vocab:
            return np.array([], dtype=np.float32)

        vec = np.zeros(len(self.vocab), dtype=np.float32)
        if not tokens:
            return vec

        tf = Counter(tokens)
        max_tf = max(tf.values())

        for tok, count in tf.items():
            idx = self.vocab.get(tok)
            if idx is None:
                continue
            # Normalized term frequency
            tf_val = count / max_tf
            # Inverse document frequency (smooth)
            df = self.doc_freq.get(idx, 1)
            idf_val = math.log((self.num_docs + 1) / (df + 1)) + 1.0
            vec[idx] = tf_val * idf_val

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    # -- Similarity ------------------------------------------------------------

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors."""
        if a.size == 0 or b.size == 0:
            return 0.0
        dot = float(np.dot(a, b))
        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def batch_cosine_similarity(
        query_vec: np.ndarray, candidates: list[tuple[int, np.ndarray]]
    ) -> list[tuple[int, float]]:
        """Compute cosine similarity between query and many candidates.

        Args:
            query_vec: Query vector (1-D).
            candidates: List of (chunk_id, vector) pairs.

        Returns:
            List of (chunk_id, score) sorted descending by score.
        """
        results: list[tuple[int, float]] = []
        for cid, vec in candidates:
            score = TfidfEmbedder.cosine_similarity(query_vec, vec)
            results.append((cid, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    # -- Serialization ---------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize embedder state for database storage."""
        return {
            "vocab": self.vocab.copy(),
            "doc_freq": {str(k): v for k, v in self.doc_freq.items()},
            "num_docs": self.num_docs,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore embedder state from a dictionary."""
        self.vocab = data.get("vocab", {})
        self.doc_freq = {int(k): v for k, v in data.get("doc_freq", {}).items()}
        self.num_docs = data.get("num_docs", 0)


# ---------------------------------------------------------------------------
# Vector serialization helpers
# ---------------------------------------------------------------------------


def serialize_vector(vec: np.ndarray) -> bytes:
    """Serialize a numpy vector to bytes for SQLite BLOB storage."""
    return vec.tobytes()


def deserialize_vector(data: bytes) -> np.ndarray:
    """Deserialize a numpy vector from SQLite BLOB."""
    return np.frombuffer(data, dtype=np.float32)
