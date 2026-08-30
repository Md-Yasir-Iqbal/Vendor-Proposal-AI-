"""
Embedding provider used to turn proposal chunks and queries into vectors
for storage/search in Chroma.

Primary path: Chroma's bundled DefaultEmbeddingFunction (all-MiniLM-L6-v2
via onnxruntime) -- a small, currently-maintained, non-deprecated local
embedding model. It downloads its weights on first use, which requires
internet access once.

Fallback path: if that model cannot be loaded (e.g. no internet access in
a locked-down environment), we fall back to a deterministic, dependency-free
hashing-based embedding so the application keeps working end-to-end
(semantic quality is reduced, and this is clearly logged/surfaced).
"""
from __future__ import annotations

import hashlib
import math
from typing import List, Optional

from app.utils.logging import get_logger

logger = get_logger("embeddings")

HASH_EMBEDDING_DIM = 384  # matches MiniLM's output dimension for interface consistency


class EmbeddingProvider:
    """Wraps whichever embedding backend is actually available."""

    def __init__(self, force_hash_fallback: bool = False):
        self._backend = None
        self._mode = "uninitialized"
        self._force_hash_fallback = force_hash_fallback

    def _init_backend(self) -> None:
        if self._backend is not None or self._mode == "hash":
            return
        if self._force_hash_fallback:
            self._mode = "hash"
            logger.info("Using deterministic hash-based embeddings (forced fallback mode).")
            return
        try:
            from chromadb.utils import embedding_functions

            self._backend = embedding_functions.DefaultEmbeddingFunction()
            # Smoke-test it once; some environments fail only at call time (e.g. no internet).
            self._backend(["smoke test"])
            self._mode = "minilm"
            logger.info("Using ONNX MiniLM embeddings (chromadb DefaultEmbeddingFunction).")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not initialize the default embedding model (%s). "
                "Falling back to a lightweight hash-based embedding. "
                "Semantic search quality will be reduced.",
                exc,
            )
            self._backend = None
            self._mode = "hash"

    @property
    def mode(self) -> str:
        self._init_backend()
        return self._mode

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._init_backend()
        if self._mode == "minilm":
            try:
                return [list(map(float, v)) for v in self._backend(texts)]
            except Exception as exc:  # noqa: BLE001
                logger.warning("MiniLM embedding call failed at runtime (%s); switching to hash fallback.", exc)
                self._mode = "hash"
        return [self._hash_embed(t) for t in texts]

    @staticmethod
    def _hash_embed(text: str, dim: int = HASH_EMBEDDING_DIM) -> List[float]:
        """A simple, deterministic bag-of-words hashing embedding. No model
        download and no external dependency required; used only as a
        last-resort fallback."""
        vec = [0.0] * dim
        tokens = text.lower().split()
        if not tokens:
            return vec
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
