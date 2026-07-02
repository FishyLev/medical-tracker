from fastapi import APIRouter

from app.models.api import UserCreateRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])
user_service = UserService()


@router.post("", response_model=UserResponse)
def create_user(payload: UserCreateRequest) -> UserResponse:
    user = user_service.create_user(
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        preferences=payload.preferences,
    )
    return UserResponse(**user)