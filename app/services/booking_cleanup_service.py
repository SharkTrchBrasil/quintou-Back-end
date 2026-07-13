"""
Serviço para limpar bookings pendentes expirados.

Este serviço deve ser executado periodicamente (ex: a cada 5 minutos) via cron job ou task scheduler.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.booking import Booking, BookingStatus
from app.database import get_db
import asyncio

class BookingCleanupService:
    """
    Cancela bookings pendentes que não foram pagos dentro do prazo.
    """
    
    # Tempo máximo que um booking pode ficar pendente (em minutos)
    PENDING_TIMEOUT_MINUTES = 15
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def cancel_expired_pending_bookings(self) -> int:
        """
        Cancela todos os bookings pendentes que expiraram.
        
        Returns:
            Número de bookings cancelados
        """
        expiration_time = datetime.now(timezone.utc) - timedelta(minutes=self.PENDING_TIMEOUT_MINUTES)
        
        # Buscar bookings pendentes criados há mais de X minutos
        query = select(Booking).where(
            Booking.status == BookingStatus.PENDING,
            Booking.created_at < expiration_time
        )
        
        result = await self.db.execute(query)
        expired_bookings = result.scalars().all()
        
        cancelled_count = 0
        for booking in expired_bookings:
            booking.status = BookingStatus.CANCELLED_BY_HOST
            booking.cancellation_reason = f"Booking expired after {self.PENDING_TIMEOUT_MINUTES} minutes without payment"
            booking.cancelled_at = datetime.now(timezone.utc)
            cancelled_count += 1
        
        if cancelled_count > 0:
            await self.db.commit()
            print(f"Cancelled {cancelled_count} expired pending bookings")
        
        return cancelled_count


async def run_cleanup():
    """
    Função principal para executar a limpeza.
    Pode ser chamada via cron job ou task scheduler.
    """
    async for db in get_db():
        try:
            service = BookingCleanupService(db)
            cancelled = await service.cancel_expired_pending_bookings()
            print(f"Booking cleanup completed: {cancelled} bookings cancelled")
        except Exception as e:
            print(f"Error during booking cleanup: {e}")
        finally:
            await db.close()


if __name__ == "__main__":
    # Permite executar o script diretamente: python -m app.services.booking_cleanup_service
    asyncio.run(run_cleanup())
