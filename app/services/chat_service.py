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

    def _get_relevant_memories(self, user_id: int, query: str) -> list[dict]:
        return self.memory_service.search_relevant_memories(user_id=user_id, query=query)

    def _build_semantic_memory_context(self, memories: list[dict]) -> str:
        return "\n".join([item["document"] for item in memories])

    def _extract_symptoms(self, text: str) -> list[dict]:
        symptom_keywords = [
            "fever", "headache", "cough", "cold", "vomiting", "nausea",
            "body pain", "sore throat", "diarrhea", "fatigue", "rash",
            "chest pain", "shortness of breath"
        ]
        found = []
        lower = text.lower()
        for keyword in symptom_keywords:
            if keyword in lower:
                found.append({"name": keyword, "detected": True})
        return found

    def _classify_urgency(self, text: str) -> str:
        lower = text.lower()
        urgent_terms = [
            "chest pain", "trouble breathing", "shortness of breath",
            "seizure", "stroke", "suicidal", "uncontrolled bleeding"
        ]
        if any(term in lower for term in urgent_terms):
            return "high"

        medium_terms = [
            "fever", "vomiting", "diarrhea", "severe pain", "rash"
        ]
        if any(term in lower for term in medium_terms):
            return "medium"

        return "low"

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
        memories = self._get_relevant_memories(user_id, message)
        semantic_memory_context = self._build_semantic_memory_context(memories)

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

        return {
            "user_id": user_id,
            "session_id": active_session_id,
            "user_message": message,
            "assistant_message": assistant_message,
            "metadata": {
                "urgency": self._classify_urgency(message),
                "used_memory": len(memories) > 0,
                "extracted_symptoms": self._extract_symptoms(message),
            },
        }