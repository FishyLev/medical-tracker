from pydantic import BaseModel, Field
from typing import Optional


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(default=None, ge=0, le=120)
    gender: Optional[str] = Field(default=None, max_length=30)
    preferences: Optional[str] = Field(default=None, max_length=1000)


class UserResponse(BaseModel):
    user_id: int
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    preferences: Optional[str] = None
    created_at: str


class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    user_id: int
    session_id: str
    user_message: str
    assistant_message: str


class MemoryResponse(BaseModel):
    user: UserResponse
    conversations: list[dict]