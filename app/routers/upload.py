from pydantic import BaseModel
from fastapi import APIRouter, Depends
from app.services.upload_service import UploadService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/upload", tags=["Uploads"])

class UploadRequest(BaseModel):
    file_name: str
    file_type: str

@router.post("/presigned-url")
def get_presigned_url(request: UploadRequest, current_user: User = Depends(get_current_user)):
    upload_service = UploadService()
    return upload_service.generate_presigned_url(request.file_name, request.file_type)
