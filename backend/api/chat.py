from services.legal_service import LegalService


class ChatRouter:
    """Placeholder API router for chat endpoint."""

    def __init__(self) -> None:
        self.legal_service = LegalService()

    def post_chat(self, user_query: str, session_id: str | None = None) -> dict:
        return self.legal_service.answer_question(user_query=user_query, session_id=session_id)


router = ChatRouter()
