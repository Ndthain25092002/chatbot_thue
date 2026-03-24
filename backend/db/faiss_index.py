from config import settings


class FaissIndex:
    """FAISS index placeholder."""

    def __init__(self) -> None:
        self.index_path = settings.faiss_index_path

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Return mock search results until FAISS integration is added."""
        return [
            {
                "chunk_id": f"chunk-{i+1}",
                "content": "Nội dung pháp lý mẫu",
                "source": "van-ban-mau",
                "score": 1.0 / (i + 1),
            }
            for i in range(top_k)
        ]
