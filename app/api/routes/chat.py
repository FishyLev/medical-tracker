from fastapi import APIRouter

from app.models.api import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = chat_service.send_message(
        user_id=payload.user_id,
        message=payload.message,
        session_id=payload.session_id,
    )
    return ChatResponse(**result)