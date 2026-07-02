from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat_placeholder() -> dict:
    return {
        "message": "Chat endpoint scaffolded successfully.",
        "status": "pending_implementation",
    }