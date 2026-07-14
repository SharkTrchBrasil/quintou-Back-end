from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import stripe
import logging

from app.database import get_db
from app.models.user import User
from app.models.space import Space
from app.services import stripe_service
from app.services.payment_service import PaymentService
from app.dependencies import get_current_user
from app.config import settings
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Pagamentos"])


class StripeOnboardingResponse(BaseModel):
    url: str


class CreatePaymentRequest(BaseModel):
    booking_id: str


class CreatePaymentResponse(BaseModel):
    client_secret: str
    payment_id: str
    amount: float
    currency: str


@router.post("/create-intent", response_model=CreatePaymentResponse)
async def create_payment_intent(
    request: CreatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria PaymentIntent no Stripe para processar pagamento de booking.
    
    O frontend deve usar o client_secret para confirmar o pagamento
    com Stripe Elements ou Checkout.
    """
    payment_service = PaymentService(db)
    
    from uuid import UUID
    intent_in = PaymentIntentCreate(booking_id=UUID(request.booking_id))
    
    result = await payment_service.create_payment_intent(
        payer_id=current_user.id,
        intent_in=intent_in
    )
    
    # Busca payment criado para retornar ID
    from sqlalchemy import select
    from app.models.payment import Payment
    payment_result = await db.execute(
        select(Payment).where(Payment.booking_id == UUID(request.booking_id))
    )
    payment = payment_result.scalar_one_or_none()
    
    return CreatePaymentResponse(
        client_secret=result.client_secret,
        payment_id=str(payment.id) if payment else "",
        amount=float(result.amount),
        currency=result.currency
    )


from sqlalchemy import select

@router.post("/onboarding", response_model=StripeOnboardingResponse)
async def create_stripe_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
            await db.commit()
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
async def check_stripe_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.stripe_account_id:
        raise HTTPException(status_code=400, detail="Sem conta na Stripe vinculada.")

    is_complete = stripe_service.check_onboarding_status(current_user.stripe_account_id)
    
    if is_complete and not current_user.stripe_onboarding_complete:
        current_user.stripe_onboarding_complete = True
        await db.commit()
        
    return {"stripe_onboarding_complete": is_complete}

# Variável para armazenar IDs de eventos já processados em memória.
# Em produção real (múltiplas instâncias), usar Redis (set/get com expiração).
processed_stripe_events = set()

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
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

    event_id = event.get('id')
    if event_id:
        if event_id in processed_stripe_events:
            logger.info(f"Stripe event {event_id} already processed. Skipping.")
            return {"status": "success"}
        processed_stripe_events.add(event_id)
        # Manter o set pequeno (opcional, para não estourar memória a longo prazo)
        if len(processed_stripe_events) > 10000:
            processed_stripe_events.clear() # Forma simples. Ideal é Redis expire.

    # Atualizações da conta Connect (Anfitrião)
    if event['type'] == 'account.updated':
        account = event['data']['object']
        account_id = account['id']
        
        result = await db.execute(select(User).filter(User.stripe_account_id == account_id))
        user = result.scalar_one_or_none()
        if user:
            if len(account.get('requirements', {}).get('currently_due', [])) == 0:
                user.stripe_onboarding_complete = True
                user.stripe_account_status = "complete"
            else:
                user.stripe_onboarding_complete = False
                user.stripe_account_status = "incomplete"
            await db.commit()
            
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
                result = await db.execute(select(Booking).filter(Booking.id == UUID(booking_id)))
                booking = result.scalar_one_or_none()
                if booking:
                    # Atualiza status da reserva
                    booking.status = BookingStatus.CONFIRMED
                    
                    # Atualiza payment record
                    payment_result = await db.execute(select(Payment).filter(Payment.booking_id == booking.id))
                    payment = payment_result.scalar_one_or_none()
                    if payment:
                        payment.status = PaymentStatus.COMPLETED
                        payment.stripe_payment_intent_id = session.get('payment_intent')
                    
                    await db.commit()
                    
                    # Envia notificações
                    notification_service = NotificationService(db)
                    
                    # Notifica Guest
                    try:
                        await notification_service.create_notification(
                            user_id=booking.guest_id,
                            n_type="BOOKING_CONFIRMED",
                            title="Pagamento confirmado!",
                            body=f"Sua reserva foi confirmada com sucesso.",
                            data={"booking_id": str(booking.id)}
                        )
                    except Exception as e:
                        logger.error(f"Error sending notification to guest: {str(e)}")
                    
                    # Notifica Host
                    space_result = await db.execute(select(Space).filter(Space.id == booking.space_id))
                    space = space_result.scalar_one_or_none()
                    if space:
                        try:
                            await notification_service.create_notification(
                                user_id=space.host_id,
                                n_type="PAYMENT_RECEIVED",
                                title="Pagamento recebido!",
                                body=f"Você recebeu uma nova reserva.",
                                data={"booking_id": str(booking.id)}
                            )
                        except Exception as e:
                            logger.error(f"Error sending notification to host: {str(e)}")
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
                result = await db.execute(select(Payment).filter(Payment.booking_id == UUID(booking_id)))
                payment = result.scalar_one_or_none()
                
                if payment:
                    payment.status = PaymentStatus.COMPLETED
                    payment.stripe_payment_intent_id = payment_intent['id']
                    await db.commit()
            except Exception as e:
                logger.error(f"Error processing payment_intent.succeeded: {str(e)}")

    # Estorno completado
    elif event['type'] == 'charge.refunded':
        from app.models.payment import Payment, PaymentStatus
        
        charge = event['data']['object']
        payment_intent_id = charge.get('payment_intent')
        
        if payment_intent_id:
            result = await db.execute(select(Payment).filter(Payment.stripe_payment_intent_id == payment_intent_id))
            payment = result.scalar_one_or_none()
            if payment:
                payment.status = PaymentStatus.REFUNDED
                await db.commit()

    # Disputa (Chargeback)
    elif event['type'] == 'charge.dispute.created':
        from app.models.payment import Payment, PaymentStatus
        from app.models.booking import Booking, BookingStatus
        
        dispute = event['data']['object']
        charge_id = dispute.get('charge')
        payment_intent_id = dispute.get('payment_intent')
        
        if payment_intent_id:
            result = await db.execute(select(Payment).filter(Payment.stripe_payment_intent_id == payment_intent_id))
            payment = result.scalar_one_or_none()
            if payment:
                booking_result = await db.execute(select(Booking).filter(Booking.id == payment.booking_id))
                booking = booking_result.scalar_one_or_none()
                if booking:
                    booking.status = BookingStatus.DISPUTED
                    await db.commit()

    # Saque (Payout) Efetuado
    elif event['type'] == 'payout.paid':
        from app.models.wallet import Transaction, TransactionStatus
        payout = event['data']['object']
        payout_id = payout['id']
        
        result = await db.execute(select(Transaction).filter(Transaction.reference_id == payout_id))
        tx = result.scalar_one_or_none()
        if tx:
            tx.status = TransactionStatus.COMPLETED
            await db.commit()
            
    # Saque (Payout) Falhou
    elif event['type'] == 'payout.failed':
        from app.models.wallet import Transaction, TransactionStatus, Wallet
        payout = event['data']['object']
        payout_id = payout['id']
        
        result = await db.execute(select(Transaction).filter(Transaction.reference_id == payout_id))
        tx = result.scalar_one_or_none()
        if tx:
            tx.status = TransactionStatus.FAILED
            # Reverte o saldo para a carteira
            wallet_result = await db.execute(select(Wallet).filter(Wallet.id == tx.wallet_id))
            wallet = wallet_result.scalar_one_or_none()
            if wallet:
                wallet.available_balance += tx.amount
            await db.commit()

    return {"status": "success"}
