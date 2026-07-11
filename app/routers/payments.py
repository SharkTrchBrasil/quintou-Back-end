from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import stripe

from app.database import get_db
from app.models.user import User
from app.services import stripe_service
from app.dependencies import get_current_user
from app.config import settings

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
            else:
                user.stripe_onboarding_complete = False
            db.commit()
            
    # Checkout completado (Reserva Paga)
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        
        # Aqui você buscaria a Booking pelo booking_id e atualizaria o status para PAGO
        # booking = db.query(Booking).filter(Booking.id == booking_id).first()
        # booking.status = 'CONFIRMED'
        # db.commit()
        pass

    return {"status": "success"}
