from api.chat import router as chat_router


def create_app() -> dict:
    """Application factory placeholder.

    Replace this return type with Flask/FastAPI app object in implementation phase.
    """
    return {
        "name": "legal-chatbot-backend",
        "routes": [chat_router],
    }


app = create_app()
