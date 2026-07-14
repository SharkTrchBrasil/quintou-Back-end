import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi import HTTPException

from app.models.user import User
from app.models.space import Space
from app.models.booking import Booking
from app.models.report import Report, ReportStatus
from app.models.payment import Payment, PaymentStatus
from app.schemas.admin import DashboardStats

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def get_dashboard_stats(self) -> DashboardStats:
        # Total Users
        users_result = await self.db.execute(select(func.count(User.id)))
        total_users = users_result.scalar() or 0
        
        # Total Spaces
        spaces_result = await self.db.execute(select(func.count(Space.id)))
        total_spaces = spaces_result.scalar() or 0
        
        # Pending Spaces
        pending_result = await self.db.execute(select(func.count(Space.id)).where(Space.is_approved == False))
        pending_spaces = pending_result.scalar() or 0
        
        # Total Bookings
        bookings_result = await self.db.execute(select(func.count(Booking.id)))
        total_bookings = bookings_result.scalar() or 0
        
        # Open Reports
        reports_result = await self.db.execute(select(func.count(Report.id)).where(Report.status == ReportStatus.OPEN))
        open_reports = reports_result.scalar() or 0
        
        # Total Revenue Platform
        revenue_result = await self.db.execute(
            select(func.sum(Payment.platform_fee)).where(Payment.status == PaymentStatus.COMPLETED)
        )
        total_revenue = revenue_result.scalar() or 0.0
        
        return DashboardStats(
            total_users=total_users,
            total_spaces=total_spaces,
            total_bookings=total_bookings,
            pending_spaces=pending_spaces,
            open_reports=open_reports,
            total_revenue_platform=float(total_revenue)
        )
        
    async def approve_space(self, space_id: uuid.UUID) -> Space:
        result = await self.db.execute(select(Space).where(Space.id == space_id))
        space = result.scalars().first()
        if not space:
            raise HTTPException(status_code=404, detail="Espaço não encontrado")
            
        space.is_approved = True
        await self.db.commit()
        await self.db.refresh(space)
        return space

    async def ban_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
            
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
