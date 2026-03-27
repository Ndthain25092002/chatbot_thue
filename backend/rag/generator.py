from config import settings


class Generator:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.generator_model

    def generate_answer(self, question: str, contexts: list[dict]) -> dict:
        """Generate answer from context chunks.

        TODO: call LLM provider and enforce legal answer format with citations.
        """
        return {
            "answer": "[MVP] Đây là câu trả lời mẫu. Cần tích hợp LLM để tạo câu trả lời thực.",
            "sources": contexts,
            "confidence": 0.0,
        }
