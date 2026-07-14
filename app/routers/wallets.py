from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import uuid

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.services.wallet_service import WalletService
from app.schemas.wallet import WalletOut, TransactionOut, PayoutRequest

router = APIRouter(prefix="/wallet", tags=["Carteira"])

@router.get("/balance", response_model=WalletOut)
async def get_wallet_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet_service = WalletService(db)
    wallet = await wallet_service.get_or_create_wallet(current_user.id)
    return wallet

@router.get("/transactions", response_model=Dict[str, Any])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    wallet_service = WalletService(db)
    wallet = await wallet_service.get_or_create_wallet(current_user.id)
    
    transactions, total = await wallet_service.get_transactions(wallet.id, skip=skip, limit=limit)
    
    # Precisamos serializar manualmente pq TransactionOut usa from_attributes
    items = [TransactionOut.model_validate(t).model_dump() for t in transactions]
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.post("/payout", response_model=TransactionOut)
async def request_payout(
    request: PayoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_host:
        raise HTTPException(status_code=403, detail="Apenas anfitriões podem solicitar saques.")
        
    wallet_service = WalletService(db)
    transaction = await wallet_service.request_payout(current_user.id, request.amount)
    
    return transaction
