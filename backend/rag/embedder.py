from config import settings


class Embedder:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model

    def embed_query(self, text: str) -> list[float]:
        """Return vector embedding for query.

        TODO: integrate sentence-transformers or external embedding API.
        """
        return [0.0] * 384

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]
