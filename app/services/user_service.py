from fastapi import HTTPException

from app.repositories.users import UserRepository


class UserService:
    def __init__(self) -> None:
        self.user_repository = UserRepository()

    def create_user(self, name: str, age: int | None, gender: str | None, preferences: str | None) -> dict:
        return self.user_repository.create_user(name=name, age=age, gender=gender, preferences=preferences)

    def get_user(self, user_id: int) -> dict:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user