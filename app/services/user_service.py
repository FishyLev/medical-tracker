from fastapi import HTTPException

from app.repositories.users import UserRepository
from app.services.memory_service import MemoryService


class UserService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()
        self.memory_service = MemoryService()

    def create_user(self, name: str, age: int | None, gender: str | None, preferences: str | None) -> dict:
        user = self.user_repository.create_user(
            name=name,
            age=age,
            gender=gender,
            preferences=preferences,
        )
        self.memory_service.remember_user_profile(user)
        return user

    def get_user(self, user_id: int) -> dict:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user