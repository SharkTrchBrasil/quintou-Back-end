from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.report import Report
from app.schemas.report import ReportCreate

class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(self, reporter_id: UUID, report_in: ReportCreate) -> Report:
        if not report_in.reported_user_id and not report_in.reported_space_id:
            raise HTTPException(status_code=400, detail="Must report either a user or a space.")
            
        report = Report(
            reporter_id=reporter_id,
            reported_user_id=report_in.reported_user_id,
            reported_space_id=report_in.reported_space_id,
            reason=report_in.reason,
            description=report_in.description
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report
