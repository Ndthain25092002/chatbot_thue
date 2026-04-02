from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from services.legal_service import LegalService


router = APIRouter(tags=["chat"])
_legal_service = LegalService()


class ChatRequest(BaseModel):
	user_query: str | None = Field(default=None, description="User question")
	message: str | None = Field(default=None, description="Alias for user_query")
	session_id: str | None = Field(default=None, description="Optional chat session id")


class ChatResponse(BaseModel):
	answer: str
	sources: list[dict] = Field(default_factory=list)
	confidence: float = 0.0
	model: str | None = None


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
	query = (payload.user_query or payload.message or "").strip()
	if not query:
		raise HTTPException(status_code=400, detail="user_query hoac message la bat buoc")

	result = _legal_service.answer_question(user_query=query, session_id=payload.session_id)
	return ChatResponse(
		answer=str(result.get("answer") or ""),
		sources=list(result.get("sources") or []),
		confidence=float(result.get("confidence") or 0.0),
		model=result.get("model"),
	)

