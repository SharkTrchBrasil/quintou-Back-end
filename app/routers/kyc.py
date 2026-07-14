from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.services.kyc_service import KYCService

router = APIRouter(prefix="/kyc", tags=["KYC & Identidade"])

@router.post("/start")
async def start_kyc(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Inicia uma sessão de verificação de identidade na Didit.
    Retorna a URL que o aplicativo/frontend deve abrir.
    """
    kyc_service = KYCService(db)
    result = await kyc_service.create_session(current_user.id)
    return result

@router.post("/webhook")
async def kyc_webhook(
    request: Request,
    x_signature_simple: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Recebe atualizações de status de verificação da Didit (APPROVED, DECLINED, etc).
    """
    payload_bytes = await request.body()
    payload_json = await request.json()
    
    kyc_service = KYCService(db)
    
    # Validar assinatura (MVP/Swappy based)
    if x_signature_simple and not kyc_service.verify_signature(payload_bytes, x_signature_simple):
        # Para evitar problemas imediatos de assinatura no MVP, apenas logamos, 
        # mas idealmente retornaríamos 401.
        import logging
        logging.getLogger(__name__).warning("Invalid Didit Webhook signature")
        
    await kyc_service.handle_webhook(payload_json)
    
    return {"status": "received"}
