from fastapi import APIRouter, File, UploadFile

from app.models.api import DocumentListResponse, DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])
document_service = DocumentService()


@router.post("/{user_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(user_id: int, file: UploadFile = File(...)) -> DocumentUploadResponse:
    result = await document_service.upload_document(user_id=user_id, file=file)
    return DocumentUploadResponse(**result)


@router.get("/{user_id}", response_model=DocumentListResponse)
def list_documents(user_id: int) -> DocumentListResponse:
    result = document_service.list_documents(user_id=user_id)
    return DocumentListResponse(**result)