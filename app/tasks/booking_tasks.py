import asyncio
from celery import shared_task
from app.services.booking_cleanup_service import run_cleanup

@shared_task(name="app.tasks.booking_tasks.cleanup_expired_bookings")
def cleanup_expired_bookings():
    """
    Task executada pelo Celery Beat para limpar reservas pendentes expiradas.
    """
    asyncio.run(run_cleanup())

async def _expire_promotions():
    from app.database import get_db
    from sqlalchemy.future import select
    from app.models.promotion import SpacePromotion
    from datetime import datetime, timezone
    
    async for db in get_db():
        try:
            now = datetime.now(timezone.utc)
            query = select(SpacePromotion).where(
                SpacePromotion.is_active == True,
                SpacePromotion.end_date < now
            )
            result = await db.execute(query)
            promotions = result.scalars().all()
            
            for promo in promotions:
                promo.is_active = False
                
            if promotions:
                await db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in expire_promotions: {e}")
        finally:
            await db.close()

@shared_task(name="app.tasks.booking_tasks.expire_promotions")
def expire_promotions():
    """ Inativa promoções cuja data de fim já passou. """
    asyncio.run(_expire_promotions())
