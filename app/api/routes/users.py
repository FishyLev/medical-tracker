from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["user"])


@router.post("")
def create_user_placeholder() -> dict:
    return {
        "message": "User endpoint scaffolded successfully.",
        "status": "pending_implementation",
    }