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
    async def event_generator():
        try:
            result = await asyncio.to_thread(
                chat_service.send_message,
                payload.user_id,
                payload.message,
                payload.session_id,
            )

            text = result.get("assistant_message", "")
            session_id = result.get("session_id")

            yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id})}\n\n"

            chunk_size = 30
            built = ""
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                built += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full_content': built})}\n\n"
                await asyncio.sleep(0.02)

            yield f"data: {json.dumps({'type': 'done', 'payload': result})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )