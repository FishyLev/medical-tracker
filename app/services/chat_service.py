import logging
import uuid

from app.repositories.conversations import ConversationRepository
from app.services.document_service import DocumentService
from app.services.local_llm import (
    generate_crisis_response,
    generate_with_provider,
    is_crisis_query,
)
from app.services.memory_service import MemoryService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


TRIAGE_SYSTEM_PROMPT = (
    "You are a cautious medical triage assistant. "
    "Respond naturally and conversationally, like an ongoing chat. "
    "Only greet the user on the very first assistant message of a new conversation. "
    "Do not start every reply with phrases like 'Hello there', 'Hi', or 'I understand'. "
    "After the first turn, continue directly based on the previous context. "
    "Do not use section headers such as 'Urgency', 'Summary', or 'Next steps'. "
    "Explain concern in plain language such as 'this should be checked soon' or "
    "'this can often be managed at home for now'. "
    "Give practical, complete advice in concise language. "
    "Provide general educational guidance only, avoid certain diagnosis, "
    "and recommend professional help when needed. "
    "If symptoms suggest urgent danger, clearly recommend immediate medical attention."
)

TRIAGE_CONTEXT = (
    "Write a natural patient-facing response. "
    "Use one short paragraph followed by 2 to 5 practical bullet points when helpful. "
    "Do not use section headers. "
    "Do not mention internal classifications like urgency levels. "
    "Do not leave incomplete bullet points. "
    "Do not abruptly cut off. "
    "Sound calm, professional, and continuous across messages."
)


class ChatService:
    def __init__(self) -> None:
        self.user_service = UserService()
        self.conversation_repository = ConversationRepository()
        self.memory_service = MemoryService()
        self.document_service = DocumentService()

    def _build_user_context(self, user: dict) -> str:
        return (
            f"Name: {user['name']}\n"
            f"Age: {user.get('age')}\n"
            f"Gender: {user.get('gender')}\n"
            f"Preferences: {user.get('preferences')}"
        )

    def _build_recent_conversation_context(self, user_id: int, limit: int = 6) -> str:
        messages = self.conversation_repository.get_user_conversations(user_id)
        recent = messages[-limit:]
        return "\n".join([f"{m['role']}: {m['message']}" for m in recent])

    def _get_relevant_memories(self, user_id: int, query: str) -> list[dict]:
        memories = self.memory_service.search_relevant_memories(
            user_id=user_id,
            query=query,
        )
        return memories[:3]

    def _build_semantic_memory_context(self, memories: list[dict]) -> str:
        return "\n".join([item["document"] for item in memories])

    def _extract_symptoms(self, text: str) -> list[dict]:
        symptom_keywords = [
            "fever",
            "headache",
            "cough",
            "cold",
            "vomiting",
            "nausea",
            "body pain",
            "sore throat",
            "diarrhea",
            "fatigue",
            "rash",
            "chest pain",
            "shortness of breath",
            "runny nose",
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
            "chest pain",
            "trouble breathing",
            "shortness of breath",
            "seizure",
            "stroke",
            "suicidal",
            "uncontrolled bleeding",
        ]
        if any(term in lower for term in urgent_terms):
            return "high"

        medium_terms = [
            "fever",
            "vomiting",
            "diarrhea",
            "severe pain",
            "rash",
        ]
        if any(term in lower for term in medium_terms):
            return "medium"

        return "low"

    def _is_first_turn(self, user_id: int) -> bool:
        messages = self.conversation_repository.get_user_conversations(user_id)
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        return len(assistant_messages) == 0

    def _build_triage_prompt(
        self,
        message: str,
        user_context: str,
        conversation_context: str,
        semantic_memory_context: str,
        document_context: str,
        first_turn: bool,
    ) -> str:
        parts = [
            f"First assistant turn: {'yes' if first_turn else 'no'}",
            "",
            "User profile:",
            user_context or "None",
            "",
            "Recent conversation:",
            conversation_context or "None",
            "",
            "Relevant memories:",
            semantic_memory_context or "None",
            "",
            "Document context:",
            document_context or "None",
            "",
            "Current user message:",
            message,
        ]
        return "\n".join(parts)

    def _generate_triage_message(
        self,
        message: str,
        user_context: str,
        conversation_context: str,
        semantic_memory_context: str,
        document_context: str,
        first_turn: bool,
    ) -> str:
        if is_crisis_query(message):
            return generate_crisis_response(message)

        triage_input = self._build_triage_prompt(
            message=message,
            user_context=user_context,
            conversation_context=conversation_context,
            semantic_memory_context=semantic_memory_context,
            document_context=document_context,
            first_turn=first_turn,
        )

        return generate_with_provider(
            system_prompt=TRIAGE_SYSTEM_PROMPT,
            context_label="Triage instructions",
            context=TRIAGE_CONTEXT,
            user_message=triage_input,
            temperature=0.2,
            max_tokens=450,
        )

    def send_message(
        self,
        user_id: int,
        message: str,
        session_id: str | None = None,
    ) -> dict:
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
        document_context = self.document_service.get_recent_document_context(user_id)
        first_turn = self._is_first_turn(user_id)

        logger.info(
            "Generating triage assistant reply",
            extra={
                "user_id": user_id,
                "session_id": active_session_id,
                "used_memory": len(memories) > 0,
                "has_document_context": bool(document_context and document_context.strip()),
                "first_turn": first_turn,
            },
        )

        assistant_message = self._generate_triage_message(
            message=message,
            user_context=user_context,
            conversation_context=conversation_context,
            semantic_memory_context=semantic_memory_context,
            document_context=document_context,
            first_turn=first_turn,
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
            "metadata": {
                "stage": "triage",
                "urgency": self._classify_urgency(message),
                "used_memory": len(memories) > 0,
                "extracted_symptoms": self._extract_symptoms(message),
            },
        }
