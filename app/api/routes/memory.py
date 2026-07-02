from fastapi import APIRouter

from app.models.api import DeleteMemoryResponse, MemoryResponse
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])
memory_service = MemoryService()


@router.get("/{user_id}", response_model=MemoryResponse)
def get_memory(user_id: int) -> MemoryResponse:
    result = memory_service.get_memory(user_id)
    return MemoryResponse(**result)


@router.delete("/{user_id}", response_model=DeleteMemoryResponse)
def delete_memory(user_id: int) -> DeleteMemoryResponse:
    result = memory_service.delete_memory(user_id)
    return DeleteMemoryResponse(**result)