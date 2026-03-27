from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer

from config import settings


class Embedder:
    """Embedding service for queries and documents using multilingual-e5-base."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load embedding model to avoid heavy startup cost."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """Return normalized embedding vector for a user query."""
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        # e5 family expects explicit task prefixes.
        encoded = self.model.encode(
            [f"query: {cleaned}"],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return encoded[0].tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return normalized embedding vectors for document chunks."""
        if not texts:
            return []

        prepared = [f"passage: {(text or '').strip()}" for text in texts]
        encoded = self.model.encode(
            prepared,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False,
        )
        return encoded.tolist()
