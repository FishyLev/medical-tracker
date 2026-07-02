from app.repositories.conversations import ConversationRepository
from app.repositories.users import UserRepository


class MemoryRepository:
    def __init__(self) -> None:
        self.user_repository = UserRepository()
        self.conversation_repository = ConversationRepository()

    def get_memory_bundle(self, user_id: int) -> dict | None:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return None

        sessions = self.conversation_repository.get_session_summaries(user_id)
        conversations = self.conversation_repository.get_user_conversations(user_id)

        return {
            "user": user,
            "sessions": sessions,
            "conversations": conversations,
        }

    def delete_memory_bundle(self, user_id: int) -> dict | None:
        user = self.user_repository.get_user_by_id(user_id)
        if not user:
            return None

        deleted_messages = self.conversation_repository.delete_user_conversations(user_id)

        return {
            "user_id": user_id,
            "deleted_messages": deleted_messages,
            "status": "ok",
        }