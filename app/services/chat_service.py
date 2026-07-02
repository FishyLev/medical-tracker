import uuid

from app.services.user_service import UserService
from app.repositories.conversations import ConversationRepository


class ChatService:
    def __init__(self) -> None:
        self.user_service = UserService()
        self.conversation_repository = ConversationRepository()

    def send_message(self, user_id: int, message: str, session_id: str | None = None) -> dict:
        user = self.user_service.get_user(user_id)
        active_session_id = session_id or str(uuid.uuid4())

        self.conversation_repository.add_message(
            user_id=user_id,
            session_id=active_session_id,
            role="user",
            message=message,
        )

        assistant_message = (
            f"I'm sorry you're not feeling well, {user['name']}. "
            f"How long have you had these symptoms? "
            f"Do you also have cough, cold, vomiting, body pain, or breathing difficulty? "
            f"If symptoms are severe or worsening, please consult a qualified doctor."
        )

        self.conversation_repository.add_message(
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