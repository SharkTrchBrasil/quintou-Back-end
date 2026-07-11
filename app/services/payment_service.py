import stripe
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.config import settings
from app.models.booking import Booking
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_payment_intent(self, payer_id: UUID, intent_in: PaymentIntentCreate) -> PaymentIntentResponse:
        # Recupera booking
        booking = await self.db.get(Booking, intent_in.booking_id)
        if not booking or booking.guest_id != payer_id:
            raise HTTPException(status_code=404, detail="Booking not found or unauthorized.")
            
        # Aqui integraríamos de fato com a API do Stripe
        # Este é apenas um stub simulado já que não temos a account conectada no setup
        try:
            # Exemplo de payload para o Stripe
            amount_cents = int(booking.total_price * 100)
            
            # payment_intent = stripe.PaymentIntent.create(
            #     amount=amount_cents,
            #     currency="brl",
            #     # Em Split payment (Connect):
            #     # transfer_data={"destination": host.stripe_account_id},
            #     # application_fee_amount=int(booking.service_fee * 100) + int(booking.host_fee * 100),
            #     metadata={"booking_id": str(booking.id)}
            # )
            
            # Mock de resposta
            client_secret = "pi_mocked_secret"
            
            # Registra no BD
            db_payment = Payment(
                booking_id=booking.id,
                payer_id=payer_id,
                amount=booking.total_price,
                platform_fee=booking.service_fee + booking.host_fee,
                host_amount=booking.host_payout,
                status=PaymentStatus.PENDING,
                stripe_payment_intent_id="pi_mocked"
            )
            self.db.add(db_payment)
            await self.db.commit()
            
            return PaymentIntentResponse(
                client_secret=client_secret,
                amount=booking.total_price,
                currency="brl"
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
