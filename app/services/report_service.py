import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.report import Report
from app.schemas.report import ReportCreate

class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_report(self, reporter_id: uuid.UUID, report_in: ReportCreate) -> Report:
        if not report_in.reported_user_id and not report_in.reported_space_id:
            raise HTTPException(status_code=400, detail="Você deve denunciar um usuário ou um espaço.")
            
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
        
        # Aqui, na Fase 6, um sinal seria enviado para os admins.
        # Caso envolva uma reserva atual, podemos também emitir um evento
        # para pausar a transferência de pagamentos.
        
        return report
        
    async def get_my_reports(self, reporter_id: uuid.UUID, skip: int = 0, limit: int = 20) -> Tuple[List[Report], int]:
        query = select(Report).where(Report.reporter_id == reporter_id).order_by(Report.created_at.desc())
        
        result = await self.db.execute(query.offset(skip).limit(limit))
        reports = result.scalars().all()
        
        from sqlalchemy import func
        count_query = select(func.count(Report.id)).where(Report.reporter_id == reporter_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(reports), total
