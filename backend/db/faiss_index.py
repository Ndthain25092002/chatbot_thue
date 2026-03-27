import json
import os
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np

from config import settings


class FaissIndex:
    """Semantic search via FAISS with metadata persistence."""

    def __init__(self) -> None:
        self.index_path = Path(settings.faiss_index_path)
        self.metadata_path = self.index_path.with_suffix(".meta.json")
        self.index: faiss.Index | None = None
        self.metadata: List[Dict[str, Any]] = []
        self.dimension = 768  # e5-base vector dimension
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Initialize or load existing FAISS index."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with self.metadata_path.open("r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception:
                self._create_fresh_index()
        else:
            self._create_fresh_index()

    def _create_fresh_index(self) -> None:
        """Create a fresh FAISS index for similarity search."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def add_documents(
        self,
        embeddings: List[List[float]],
        metadatas: List[Dict[str, str]],
    ) -> None:
        """Add document embeddings and metadata to index."""
        if not embeddings or not metadatas:
            return

        if len(embeddings) != len(metadatas):
            raise ValueError("Number of embeddings and metadatas must match")

        embeddings_array = np.array(embeddings, dtype=np.float32)
        if embeddings_array.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {embeddings_array.shape[1]} "
                f"does not match index dimension {self.dimension}"
            )

        self.index.add(embeddings_array)
        self.metadata.extend(metadatas)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for top-k most similar documents."""
        if not query_embedding or not self.metadata:
            return []

        query_array = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query_array, top_k)
        scores = scores[0]
        indices = indices[0]

        results = []
        for idx, score in zip(indices, scores):
            if 0 <= idx < len(self.metadata):
                result = dict(self.metadata[int(idx)])
                result["score"] = float(score)
                results.append(result)
        return results

    def save(self) -> None:
        """Persist index and metadata to disk."""
        if self.index is None or not self.metadata:
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))

        with self.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self) -> bool:
        """Load index and metadata from disk."""
        try:
            if self.index_path.exists() and self.metadata_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                with self.metadata_path.open("r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                return True
        except Exception:
            pass
        return False

    def clear(self) -> None:
        """Reset index and remove persisted files."""
        self._create_fresh_index()
        if self.index_path.exists():
            self.index_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()

    def get_size(self) -> int:
        """Return number of vectors in index."""
        return self.index.ntotal if self.index else 0
