from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.payment import PaymentIntentCreate, PaymentIntentResponse
from app.models.user import User
from app.dependencies import get_current_user
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Pagamentos"])

@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    intent_in: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    payment_service = PaymentService(db)
    return await payment_service.create_payment_intent(current_user.id, intent_in)
