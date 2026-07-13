from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe
import logging

from app.database import get_db
from app.models.user import User
from app.models.space import Space
from app.services import stripe_service
from app.dependencies import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Pagamentos"])

class StripeOnboardingResponse(BaseModel):
    url: str

@router.post("/onboarding", response_model=StripeOnboardingResponse)
def create_stripe_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_host:
        raise HTTPException(status_code=403, detail="Apenas anfitriões podem acessar o onboarding da Stripe.")
        
    if not current_user.cpf:
        raise HTTPException(status_code=400, detail="CPF é obrigatório para o onboarding na Stripe. Atualize seu perfil.")

    # Se ainda não tem conta Stripe, cria
    if not current_user.stripe_account_id:
        try:
            first_name = current_user.full_name.split(" ")[0]
            last_name = " ".join(current_user.full_name.split(" ")[1:]) if len(current_user.full_name.split(" ")) > 1 else first_name
            
            account_id = stripe_service.create_connect_account(
                email=current_user.email,
                first_name=first_name,
                last_name=last_name,
                cpf=current_user.cpf
            )
            current_user.stripe_account_id = account_id
            db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao criar conta na Stripe: {str(e)}")

    # URLs de retorno para o app via Deep Link
    return_url = "quintou://stripe/success" 
    refresh_url = "quintou://stripe/refresh"

    try:
        url = stripe_service.generate_onboarding_link(
            account_id=current_user.stripe_account_id,
            return_url=return_url,
            refresh_url=refresh_url
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar link da Stripe: {str(e)}")

@router.get("/onboarding/status")
def check_stripe_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.stripe_account_id:
        raise HTTPException(status_code=400, detail="Sem conta na Stripe vinculada.")

    is_complete = stripe_service.check_onboarding_status(current_user.stripe_account_id)
    
    if is_complete and not current_user.stripe_onboarding_complete:
        current_user.stripe_onboarding_complete = True
        db.commit()
        
    return {"stripe_onboarding_complete": is_complete}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Atualizações da conta Connect (Anfitrião)
    if event['type'] == 'account.updated':
        account = event['data']['object']
        account_id = account['id']
        
        user = db.query(User).filter(User.stripe_account_id == account_id).first()
        if user:
            if len(account.get('requirements', {}).get('currently_due', [])) == 0:
                user.stripe_onboarding_complete = True
                user.stripe_account_status = "complete"
            else:
                user.stripe_onboarding_complete = False
                user.stripe_account_status = "incomplete"
            db.commit()
            
    # Checkout completado (Reserva Paga)
    elif event['type'] == 'checkout.session.completed':
        from app.models.booking import Booking, BookingStatus
        from app.models.payment import Payment, PaymentStatus
        from app.services.notification_service import NotificationService
        from uuid import UUID
        
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        
        if booking_id:
            try:
                booking = db.query(Booking).filter(Booking.id == UUID(booking_id)).first()
                if booking:
                    # Atualiza status da reserva
                    booking.status = BookingStatus.CONFIRMED
                    
                    # Atualiza payment record
                    payment = db.query(Payment).filter(Payment.booking_id == booking.id).first()
                    if payment:
                        payment.status = PaymentStatus.COMPLETED
                        payment.stripe_payment_intent_id = session.get('payment_intent')
                    
                    db.commit()
                    
                    # Envia notificações
                    notification_service = NotificationService(db)
                    
                    # Notifica Guest
                    await notification_service.create_notification(
                        user_id=booking.guest_id,
                        type="BOOKING_CONFIRMED",
                        title="Pagamento confirmado!",
                        body=f"Sua reserva foi confirmada com sucesso.",
                        data={"booking_id": str(booking.id)}
                    )
                    
                    # Notifica Host
                    space = db.query(Space).filter(Space.id == booking.space_id).first()
                    if space:
                        await notification_service.create_notification(
                            user_id=space.host_id,
                            type="PAYMENT_RECEIVED",
                            title="Pagamento recebido!",
                            body=f"Você recebeu uma nova reserva.",
                            data={"booking_id": str(booking.id)}
                        )
            except Exception as e:
                logger.error(f"Error processing checkout.session.completed: {str(e)}")
    
    # PaymentIntent succeeded (alternativa ao checkout.session)
    elif event['type'] == 'payment_intent.succeeded':
        from app.models.payment import Payment, PaymentStatus
        from uuid import UUID
        
        payment_intent = event['data']['object']
        booking_id = payment_intent.get('metadata', {}).get('booking_id')
        
        if booking_id:
            try:
                payment = db.query(Payment).filter(
                    Payment.booking_id == UUID(booking_id)
                ).first()
                
                if payment:
                    payment.status = PaymentStatus.COMPLETED
                    payment.stripe_payment_intent_id = payment_intent['id']
                    db.commit()
            except Exception as e:
                logger.error(f"Error processing payment_intent.succeeded: {str(e)}")

    return {"status": "success"}
