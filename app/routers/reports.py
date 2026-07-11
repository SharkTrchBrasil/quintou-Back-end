from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.report import ReportCreate, ReportResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Denúncias"])

@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_service = ReportService(db)
    return await report_service.create_report(current_user.id, report_in)
