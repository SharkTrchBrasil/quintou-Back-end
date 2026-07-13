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
        # Recupera booking com space e host
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.space import Space
        from app.models.user import User
        
        result = await self.db.execute(
            select(Booking).options(
                selectinload(Booking.space).selectinload(Space.host)
            ).where(Booking.id == intent_in.booking_id)
        )
        booking = result.scalars().first()
        
        if not booking or booking.guest_id != payer_id:
            raise HTTPException(status_code=404, detail="Booking not found or unauthorized.")
        
        host = booking.space.host
        if not host.stripe_account_id:
            raise HTTPException(
                status_code=400, 
                detail="Host has not completed Stripe onboarding. Cannot process payment."
            )
            
        try:
            # Valores em centavos (Stripe usa centavos)
            amount_cents = int(booking.total_price * 100)
            application_fee_cents = int((booking.service_fee + booking.host_fee) * 100)
            
            # Cria PaymentIntent real com Destination Charge (Stripe Connect)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="brl",
                application_fee_amount=application_fee_cents,
                transfer_data={
                    "destination": host.stripe_account_id,
                },
                metadata={
                    "booking_id": str(booking.id),
                    "guest_id": str(booking.guest_id),
                    "host_id": str(host.id),
                    "space_id": str(booking.space_id)
                },
                description=f"Reserva {booking.space.title} - {booking.date}"
            )
            
            # Registra no BD
            db_payment = Payment(
                booking_id=booking.id,
                payer_id=payer_id,
                amount=booking.total_price,
                platform_fee=booking.service_fee + booking.host_fee,
                host_amount=booking.host_payout,
                status=PaymentStatus.PENDING,
                stripe_payment_intent_id=payment_intent.id
            )
            self.db.add(db_payment)
            await self.db.commit()
            
            return PaymentIntentResponse(
                client_secret=payment_intent.client_secret,
                amount=booking.total_price,
                currency="brl"
            )
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")
