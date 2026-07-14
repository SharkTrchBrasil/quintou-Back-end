from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.report import ReportCreate, ReportResponse
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

@router.get("/my", response_model=List[ReportResponse])
async def list_my_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report_service = ReportService(db)
    reports, _ = await report_service.get_my_reports(current_user.id, skip, limit)
    return reports
