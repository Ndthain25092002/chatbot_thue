from rag.embedder import Embedder
from rag.retriever import Retriever
from rag.generator import Generator
from rag.reranker import Reranker
from services.cache_service import CacheService


class LegalService:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.retriever = Retriever()
        self.reranker = Reranker()
        self.generator = Generator()
        self.cache = CacheService()

    def answer_question(self, user_query: str, session_id: str | None = None) -> dict:
        cache_key = f"chat:{session_id}:{user_query}" if session_id else f"chat:{user_query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        query_embedding = self.embedder.embed_query(user_query)
        contexts = self.retriever.retrieve(query_embedding=query_embedding, top_k=20)
        reranked_contexts = self.reranker.rerank(user_query, contexts, top_k=5)
        result = self.generator.generate_answer(user_query, reranked_contexts)
        self.cache.set(cache_key, result)
        return result
