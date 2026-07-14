from celery import shared_task
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.future import select

from app.database import AsyncSessionLocal
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)

async def _async_release_pending_funds():
    """
    Função assíncrona que faz o trabalho pesado de liberar fundos
    para reservas que foram completadas há mais de 24 horas.
    """
    async with AsyncSessionLocal() as session:
        wallet_service = WalletService(session)
        
        # Encontra pagamentos com status COMPLETED
        # onde a reserva já foi completada há mais de 24 horas
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = (
            select(Payment)
            .join(Booking, Payment.booking_id == Booking.id)
            .where(
                Payment.status == PaymentStatus.COMPLETED,
                Booking.status == BookingStatus.COMPLETED,
                # Booking.end_time é time, Booking.date é date. 
                # Idealmente comparamos com um campo 'completed_at' ou 'end_datetime'
            )
        )
        
        # Como end_time é apenas time, vamos verificar se o check-out já passou de 24h
        # baseando-se na data do booking + end_time
        result = await session.execute(query)
        payments_to_release = result.scalars().all()
        
        released_count = 0
        for payment in payments_to_release:
            # Reconstituir o datetime final da reserva
            booking = await payment.awaitable_attrs.booking
            booking_end_dt = datetime.combine(booking.date, booking.end_time)
            booking_end_dt = booking_end_dt.replace(tzinfo=timezone.utc)
            
            if booking_end_dt <= twenty_four_hours_ago:
                try:
                    # Move da carteira pendente para a disponível
                    await wallet_service.release_funds_to_available(payment.booking_id)
                    released_count += 1
                except Exception as e:
                    logger.error(f"Error releasing funds for booking {payment.booking_id}: {str(e)}")
                    
        return released_count


@shared_task(name="app.tasks.payout_tasks.release_pending_funds")
def release_pending_funds():
    """
    Tarefa periódica (Celery Beat) para liberar fundos de reservas concluídas.
    """
    logger.info("Starting periodic task: release_pending_funds")
    count = asyncio.run(_async_release_pending_funds())
    logger.info(f"Finished periodic task. Released funds for {count} bookings.")
    return count
