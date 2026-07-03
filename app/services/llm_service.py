import logging

from google import genai
from google.genai.types import HttpOptions

from app.core.config import get_settings
from app.core.prompts import MEDICAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=HttpOptions(timeout=settings.gemini_timeout_ms),
        )

    def _fallback_reply(self, user_message: str) -> str:
        text = user_message.lower()

        if any(term in text for term in ["chest pain", "trouble breathing", "shortness of breath", "seizure", "stroke", "suicidal"]):
            return (
                "Your symptoms may need urgent medical attention. "
                "Please seek emergency or immediate in-person medical care right away."
            )

        return (
            "I’m sorry, but I’m having trouble generating a full response right now. "
            "Please monitor your symptoms, stay hydrated if appropriate, and consult a qualified doctor if symptoms are worsening, severe, or not improving."
        )

    def generate_medical_reply(
        self,
        user_message: str,
        user_context: str,
        conversation_context: str,
        semantic_memory_context: str,
        document_context: str = "",
    ) -> str:
        prompt = f"""
{MEDICAL_SYSTEM_PROMPT}

Known user context:
{user_context or 'None'}

Recent conversation context:
{conversation_context or 'None'}

Relevant long-term memory:
{semantic_memory_context or 'None'}

Uploaded medical documents:
{document_context or 'None'}

User message:
{user_message}

Respond as the medical assistant in plain text.
If the uploaded documents are relevant, use them in your answer.
If the documents are unclear or incomplete, say so.
Do not claim certainty when the document text is ambiguous.
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )

            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()

            logger.warning("Gemini returned empty text response.")
            return self._fallback_reply(user_message)

        except Exception as e:
            logger.exception("Gemini generation failed: %s", e)
            return self._fallback_reply(user_message)