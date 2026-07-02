import re
from fastapi import HTTPException

from app.repositories.memory import MemoryRepository
from app.vectorstore.chroma_store import ChromaMemoryStore


class MemoryService:
    def __init__(self) -> None:
        self.memory_repository = MemoryRepository()
        self.chroma_store = ChromaMemoryStore()

    def get_memory(self, user_id: int) -> dict:
        bundle = self.memory_repository.get_memory_bundle(user_id)
        if not bundle:
            raise HTTPException(status_code=404, detail="User not found")
        return bundle

    def delete_memory(self, user_id: int) -> dict:
        result = self.memory_repository.delete_memory_bundle(user_id)
        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        self.chroma_store.delete_user_memories(user_id)
        return result

    def remember_user_profile(self, user: dict) -> None:
        text = (
            f"User profile: name={user['name']}, age={user.get('age')}, "
            f"gender={user.get('gender')}, preferences={user.get('preferences')}"
        )
        self.chroma_store.add_memory(
            user_id=user["user_id"],
            content=text,
            memory_type="user_profile",
        )

    def _extract_facts(self, message: str) -> list[str]:
        facts = []
        text = message.strip()

        patterns = [
            r"\bmy name is ([A-Za-z ]+)",
            r"\bi am (\d{1,3}) years old\b",
            r"\bi prefer ([A-Za-z ,\-]+)",
            r"\bi have ([A-Za-z ,\-]+)",
            r"\bi am allergic to ([A-Za-z ,\-]+)",
            r"\bi have a history of ([A-Za-z ,\-]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for match in matches:
                value = match.strip()
                if value:
                    facts.append(f"User fact: {value}")

        symptom_keywords = [
            "fever", "headache", "cough", "cold", "vomiting", "nausea",
            "body pain", "sore throat", "diarrhea", "fatigue", "rash"
        ]

        for keyword in symptom_keywords:
            if keyword in text.lower():
                facts.append(f"Symptom mentioned: {keyword}")

        seen = set()
        deduped = []
        for fact in facts:
            if fact not in seen:
                seen.add(fact)
                deduped.append(fact)

        return deduped

    def remember_message(self, user_id: int, session_id: str, role: str, message: str) -> None:
        if role != "user":
            return

        facts = self._extract_facts(message)
        for fact in facts:
            self.chroma_store.add_memory(
                user_id=user_id,
                content=fact,
                memory_type="extracted_fact",
                metadata={"session_id": session_id, "role": role},
            )

    def search_relevant_memories(self, user_id: int, query: str) -> list[dict]:
        return self.chroma_store.search_memories(user_id=user_id, query=query, n_results=5)