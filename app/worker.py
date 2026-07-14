import os
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Carrega a URL do Redis da configuração
redis_url = settings.REDIS_URL

celery_app = Celery(
    "quintou_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "app.tasks.payout_tasks", 
        "app.tasks.notification_tasks", 
        "app.tasks.booking_tasks",
        "app.tasks.reminder_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Agendamentos (Celery Beat)
    beat_schedule={
        "release-pending-funds-every-hour": {
            "task": "app.tasks.payout_tasks.release_pending_funds",
            "schedule": crontab(minute=0),
        },
        "cleanup-expired-bookings-every-15-mins": {
            "task": "app.tasks.booking_tasks.cleanup_expired_bookings",
            "schedule": crontab(minute="*/15"),
        },
        "auto-complete-bookings-every-30-mins": {
            "task": "app.tasks.reminder_tasks.auto_complete_bookings",
            "schedule": crontab(minute="*/30"),
        },
        "send-reminders-daily": {
            "task": "app.tasks.reminder_tasks.send_upcoming_booking_reminders",
            "schedule": crontab(hour=12, minute=0), # Todo dia as 12h UTC
        },
    }
)
