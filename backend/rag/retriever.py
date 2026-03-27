from db.faiss_index import FaissIndex


class Retriever:
    def __init__(self) -> None:
        self.index = FaissIndex()

    def retrieve(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        return self.index.search(query_embedding=query_embedding, top_k=top_k)
