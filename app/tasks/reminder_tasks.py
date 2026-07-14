from celery import shared_task
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from app.database import get_db
from app.models.booking import Booking, BookingStatus
from app.services.notification_service import NotificationService

async def _send_reminders():
    async for db in get_db():
        try:
            notification_service = NotificationService(db)
            now = datetime.now(timezone.utc)
            target_time_start = now + timedelta(hours=23, minutes=45)
            target_time_end = now + timedelta(hours=24, minutes=15)
            
            # Simplified check (since date and start_time are separate fields)
            # In production, we'd calculate the exact datetime
            # For MVP: find bookings for tomorrow
            tomorrow = (now + timedelta(days=1)).date()
            
            query = select(Booking).where(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.date == tomorrow
            )
            result = await db.execute(query)
            bookings = result.scalars().all()
            
            for booking in bookings:
                # Notifica o Hóspede
                await notification_service.create_notification(
                    user_id=booking.guest_id,
                    n_type="BOOKING_REMINDER",
                    title="Seu espaço te espera amanhã!",
                    body="Prepare-se para sua reserva amanhã.",
                    data={"booking_id": str(booking.id)}
                )
                
                # Obtém o Space para notificar o Anfitrião
                from app.models.space import Space
                space_res = await db.execute(select(Space).where(Space.id == booking.space_id))
                space = space_res.scalars().first()
                if space:
                    await notification_service.create_notification(
                        user_id=space.host_id,
                        n_type="HOST_REMINDER",
                        title="Você tem uma reserva amanhã!",
                        body="Prepare o espaço para o hóspede amanhã.",
                        data={"booking_id": str(booking.id)}
                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in reminders: {e}")
        finally:
            await db.close()

async def _auto_complete():
    async for db in get_db():
        try:
            now = datetime.now(timezone.utc)
            today_date = now.date()
            current_time = now.time()
            
            # Encontrar bookings de dias passados, ou de hoje que já passaram do end_time
            query = select(Booking).where(
                Booking.status == BookingStatus.CONFIRMED,
                (Booking.date < today_date) | 
                ((Booking.date == today_date) & (Booking.end_time < current_time))
            )
            
            result = await db.execute(query)
            bookings = result.scalars().all()
            
            for booking in bookings:
                booking.status = BookingStatus.COMPLETED
                
            if bookings:
                await db.commit()
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in auto complete: {e}")
        finally:
            await db.close()

@shared_task(name="app.tasks.reminder_tasks.send_upcoming_booking_reminders")
def send_upcoming_booking_reminders():
    """ Envia push notifications para reservas do dia seguinte. """
    asyncio.run(_send_reminders())

@shared_task(name="app.tasks.reminder_tasks.auto_complete_bookings")
def auto_complete_bookings():
    """ Passa status de CONFIRMED para COMPLETED se o tempo já acabou. """
    asyncio.run(_auto_complete())

async def _request_reviews():
    async for db in get_db():
        try:
            notification_service = NotificationService(db)
            now = datetime.now(timezone.utc)
            yesterday_date = (now - timedelta(days=1)).date()
            
            # Buscar bookings que completaram há 24h
            query = select(Booking).where(
                Booking.status == BookingStatus.COMPLETED,
                Booking.date == yesterday_date
            )
            result = await db.execute(query)
            bookings = result.scalars().all()
            
            # Precisamos checar se já existe review. Idealmente buscar o review,
            # mas para MVP vamos disparar para todos do dia.
            from app.models.review import Review
            
            for booking in bookings:
                # Check se guest já avaliou
                review_check = await db.execute(select(Review).where(Review.booking_id == booking.id, Review.author_id == booking.guest_id))
                if not review_check.scalars().first():
                    await notification_service.create_notification(
                        user_id=booking.guest_id,
                        n_type="REVIEW_REQUEST",
                        title="Como foi sua experiência?",
                        body="Sua opinião é importante. Avalie o espaço que você reservou.",
                        data={"booking_id": str(booking.id), "space_id": str(booking.space_id)}
                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in request_reviews: {e}")
        finally:
            await db.close()

async def _weekly_host_summary():
    async for db in get_db():
        try:
            notification_service = NotificationService(db)
            now = datetime.now(timezone.utc)
            one_week_ago = (now - timedelta(days=7)).date()
            
            # Para cada host (user is_host=True), ver quantas bookings COMPLETED nos últimos 7 dias.
            from app.models.user import User
            from sqlalchemy import func
            
            hosts_query = select(User).where(User.is_host == True, User.is_active == True)
            hosts_result = await db.execute(hosts_query)
            hosts = hosts_result.scalars().all()
            
            from app.models.space import Space
            for host in hosts:
                # Pega as bookings
                bk_query = select(func.count(Booking.id), func.sum(Booking.host_payout)).select_from(Booking).join(Space).where(
                    Space.host_id == host.id,
                    Booking.status == BookingStatus.COMPLETED,
                    Booking.date >= one_week_ago
                )
                bk_res = await db.execute(bk_query)
                row = bk_res.first()
                if row and row[0] > 0:
                    count = row[0]
                    total_payout = row[1] or 0.0
                    
                    await notification_service.create_notification(
                        user_id=host.id,
                        n_type="HOST_WEEKLY_SUMMARY",
                        title="Resumo da sua semana",
                        body=f"Você teve {count} reservas completadas e ganhou R$ {total_payout:.2f}!",
                        data={"type": "summary"}
                    )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in weekly_host_summary: {e}")
        finally:
            await db.close()

@shared_task(name="app.tasks.reminder_tasks.request_reviews")
def request_reviews():
    """ Solicita avaliação 24h após a reserva. """
    asyncio.run(_request_reviews())

@shared_task(name="app.tasks.reminder_tasks.weekly_host_summary")
def weekly_host_summary():
    """ Envia resumo semanal de ganhos para os anfitriões (rodar aos domingos). """
    asyncio.run(_weekly_host_summary())
