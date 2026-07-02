import uuid

from app.repositories.conversations import ConversationRepository
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.user_service import UserService


class ChatService:
    def __init__(self) -> None:
        self.user_service = UserService()
        self.conversation_repository = ConversationRepository()
        self.memory_service = MemoryService()
        self.llm_service = LLMService()

    def _build_user_context(self, user: dict) -> str:
        return (
            f"Name: {user['name']}\n"
            f"Age: {user.get('age')}\n"
            f"Gender: {user.get('gender')}\n"
            f"Preferences: {user.get('preferences')}"
        )

    def _build_recent_conversation_context(self, user_id: int, limit: int = 8) -> str:
        messages = self.conversation_repository.get_user_conversations(user_id)
        recent = messages[-limit:]
        return "\n".join([f"{m['role']}: {m['message']}" for m in recent])

    def _build_semantic_memory_context(self, user_id: int, query: str) -> str:
        memories = self.memory_service.search_relevant_memories(user_id=user_id, query=query)
        return "\n".join([item["document"] for item in memories])

    def send_message(self, user_id: int, message: str, session_id: str | None = None) -> dict:
        user = self.user_service.get_user(user_id)
        active_session_id = session_id or str(uuid.uuid4())

        self.conversation_repository.add_message(
            user_id=user_id,
            session_id=active_session_id,
            role="user",
            message=message,
        )
        self.memory_service.remember_message(
            user_id=user_id,
            session_id=active_session_id,
            role="user",
            message=message,
        )

        user_context = self._build_user_context(user)
        conversation_context = self._build_recent_conversation_context(user_id)
        semantic_memory_context = self._build_semantic_memory_context(user_id, message)

        assistant_message = self.llm_service.generate_medical_reply(
            user_message=message,
            user_context=user_context,
            conversation_context=conversation_context,
            semantic_memory_context=semantic_memory_context,
        )

        self.conversation_repository.add_message(
            user_id=user_id,
            session_id=active_session_id,
            role="assistant",
            message=assistant_message,
        )
        self.memory_service.remember_message(
            user_id=user_id,
            session_id=active_session_id,
            role="assistant",
            message=assistant_message,
        )

        return {
            "user_id": user_id,
            "session_id": active_session_id,
            "user_message": message,
            "assistant_message": assistant_message,
        }