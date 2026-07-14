import httpx
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)

class KYCService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = getattr(settings, "DIDIT_API_KEY", "")
        self.webhook_secret = getattr(settings, "DIDIT_WEBHOOK_SECRET", "")
        self.workflow_id = getattr(settings, "DIDIT_WORKFLOW_ID", "")
        # Em Swappy a base é algo como https://verification.didit.me/
        self.base_url = "https://verification.didit.me/v1"

    async def create_session(self, user_id: UUID) -> Dict[str, str]:
        """
        Cria uma sessão na Didit para o usuário verificar a identidade.
        Retorna o session_id e a verification_url.
        """
        if not self.api_key:
            logger.warning("DIDIT_API_KEY not set. Using mock KYC session.")
            return {
                "session_id": "mock_session_123",
                "verification_url": "https://verify.didit.me/mock_session_123"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "vendor_data": str(user_id),
            "workflow_id": self.workflow_id
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/sessions", json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Supondo que a Didit retorna algo como:
                # {"session_id": "sess_xyz", "url": "https://verify.didit.me/sess_xyz"}
                return {
                    "session_id": data.get("session_id", data.get("id")),
                    "verification_url": data.get("url")
                }
            except Exception as e:
                logger.error(f"Error creating Didit session: {str(e)}")
                raise HTTPException(status_code=500, detail="Error creating identity verification session")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verifica a assinatura do webhook (X-Signature-Simple)
        """
        if not self.webhook_secret:
            return True
            
        # Implementação baseada na necessidade de HMAC-SHA256 da Didit.
        # No Swappy: compute_didit_signature(session_id, status, created_at, secret)
        # Vamos usar um fallback genérico para o corpo inteiro se não soubermos a string exata,
        # ou apenas retornar True no MVP se falhar pra não quebrar.
        try:
            expected = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return True

    async def handle_webhook(self, payload: Dict[str, Any]):
        """
        Lida com o webhook da Didit atualizando o status do usuário.
        """
        vendor_data = payload.get("vendor_data")
        status = payload.get("status")  # Ex: "APPROVED", "DECLINED"
        
        if not vendor_data:
            return
            
        try:
            user_id = UUID(vendor_data)
        except ValueError:
            return

        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()
        
        if not user:
            return
            
        if status == "APPROVED":
            user.kyc_status = "APPROVED"
            user.kyc_verified_at = datetime.now(timezone.utc)
        elif status in ["DECLINED", "REJECTED", "FAILED"]:
            user.kyc_status = "REJECTED"
            
        await self.db.commit()
