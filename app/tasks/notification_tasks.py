from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_async(self, to_email: str, subject: str, body: str):
    """
    Tarefa assíncrona para envio de e-mails usando SendGrid ou outro provedor.
    No MVP, apenas simulamos o envio com um logger.
    """
    try:
        # Aqui entra a lógica real de envio, ex: usando SendGridClient
        logger.info(f"Sending email to {to_email}: {subject}")
        # Simulando envio bem sucedido
        return {"status": "sent", "to": to_email}
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        self.retry(exc=exc, countdown=60)
