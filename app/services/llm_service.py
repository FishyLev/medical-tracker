from google import genai

from app.core.config import get_settings
from app.core.prompts import MEDICAL_SYSTEM_PROMPT


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def generate_medical_reply(
        self,
        user_message: str,
        user_context: str,
        conversation_context: str,
        semantic_memory_context: str,
    ) -> str:
        prompt = f"""
{MEDICAL_SYSTEM_PROMPT}

Known user context:
{user_context or 'None'}

Recent conversation context:
{conversation_context or 'None'}

Relevant long-term memory:
{semantic_memory_context or 'None'}

User message:
{user_message}

Respond as the medical assistant in plain text.
""".strip()

        response = self.client.models.generate_content(
            model=self.settings.gemini_model,
            contents=prompt,
        )

        return (response.text or "").strip()