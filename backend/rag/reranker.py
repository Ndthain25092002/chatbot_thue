class Reranker:
    """Optional reranker stage for improving retrieval quality."""

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        return candidates[:top_k]
