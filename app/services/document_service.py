from io import BytesIO

import PyPDF2
from fastapi import HTTPException, UploadFile

from app.repositories.documents import DocumentRepository
from app.services.user_service import UserService


class DocumentService:
    def __init__(self) -> None:
        self.user_service = UserService()
        self.document_repository = DocumentRepository()

    def _extract_text_from_pdf(self, content: bytes) -> str:
        reader = PyPDF2.PdfReader(BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts).strip()

    def _extract_text_from_txt(self, content: bytes) -> str:
        return content.decode("utf-8", errors="ignore").strip()

    def _summarize_text(self, text: str) -> str:
        cleaned = " ".join(text.split())
        return cleaned[:500] if cleaned else ""

    async def upload_document(self, user_id: int, file: UploadFile) -> dict:
        self.user_service.get_user(user_id)

        filename = file.filename or "uploaded_file"
        lower = filename.lower()
        content = await file.read()

        if lower.endswith(".pdf"):
            extracted_text = self._extract_text_from_pdf(content)
        elif lower.endswith(".txt"):
            extracted_text = self._extract_text_from_txt(content)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported in step 8.")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="No readable text could be extracted from the file.")

        summary = self._summarize_text(extracted_text)

        saved = self.document_repository.add_document(
            user_id=user_id,
            filename=filename,
            content_type=file.content_type,
            extracted_text=extracted_text[:20000],
            summary=summary,
        )

        return {
            "document_id": saved["id"],
            "user_id": saved["user_id"],
            "filename": saved["filename"],
            "content_type": saved["content_type"],
            "extracted_chars": len(saved["extracted_text"]),
            "summary": saved["summary"],
            "created_at": saved["created_at"],
        }

    def list_documents(self, user_id: int) -> dict:
        self.user_service.get_user(user_id)
        rows = self.document_repository.list_documents(user_id)
        return {
            "user_id": user_id,
            "documents": [
                {
                    "document_id": row["id"],
                    "filename": row["filename"],
                    "content_type": row["content_type"],
                    "extracted_chars": len(row["extracted_text"]),
                    "summary": row["summary"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ],
        }

    def get_recent_document_context(self, user_id: int) -> str:
        return self.document_repository.get_latest_documents_text(user_id=user_id, limit=3)