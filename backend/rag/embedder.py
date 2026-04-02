from __future__ import annotations

import os
from typing import List

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from config import settings


class Embedder:
    """Embedding service for queries and documents using multilingual-e5-base."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self._tokenizer = None
        self._model = None

        # Keep runtime deterministic and avoid thread oversubscription issues on Windows.
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        torch.set_num_threads(1)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            # Ignore if threads were already initialized.
            pass

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        return self._tokenizer

    @property
    def model(self):
        """Lazy-load embedding model to avoid heavy startup cost."""
        if self._model is None:
            self._model = AutoModel.from_pretrained(self.model_name)
            self._model.eval()
        return self._model

    def _mean_pool(self, last_hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        mask = mask.unsqueeze(-1).expand(last_hidden.size()).float()
        summed = torch.sum(last_hidden * mask, dim=1)
        counts = torch.clamp(mask.sum(dim=1), min=1e-9)
        return summed / counts

    def _encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        with torch.inference_mode():
            batch = self.tokenizer(
                texts,
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            outputs = self.model(**batch)
            embeddings = self._mean_pool(outputs.last_hidden_state, batch["attention_mask"])
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.detach().cpu().numpy().astype(np.float32).tolist()

    def embed_query(self, text: str) -> List[float]:
        """Return normalized embedding vector for a user query."""
        cleaned = (text or "").strip()
        if not cleaned:
            return []

        # e5 family expects explicit task prefixes.
        encoded = self._encode([f"query: {cleaned}"])
        return encoded[0] if encoded else []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return normalized embedding vectors for document chunks."""
        if not texts:
            return []

        prepared = [f"passage: {(text or '').strip()}" for text in texts]
        return self._encode(prepared)
