from fastapi import APIRouter

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{user_id}")
def get_memory_placeholder(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "message": "Get memory endpoint scaffolded successfully.",
        "status": "pending_implementation",
    }


@router.delete("/{user_id}")
def delete_memory_placeholder(user_id: str) -> dict:
    return {
        "user_id": user_id,
        "message": "Delete memory endpoint scaffolded successfully.",
        "status": "pending_implementation",
    }