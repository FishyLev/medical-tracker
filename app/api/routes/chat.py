import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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


@router.post("/stream")
async def chat_stream(payload: ChatRequest):
    result = chat_service.send_message(
        user_id=payload.user_id,
        message=payload.message,
        session_id=payload.session_id,
    )

    async def event_generator():
        text = result["assistant_message"]
        words = text.split()

        yield f"data: {json.dumps({'type': 'meta', 'session_id': result['session_id']})}\n\n"

        partial = []
        for word in words:
            partial.append(word)
            chunk = " ".join(partial)
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done', 'payload': result})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")