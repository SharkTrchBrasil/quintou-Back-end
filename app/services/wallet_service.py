import uuid
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
import stripe

from app.models.wallet import Wallet, Transaction, TransactionType, TransactionStatus
from app.models.user import User
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, user_id: uuid.UUID) -> Wallet:
        query = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.db.execute(query)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            wallet = Wallet(user_id=user_id)
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)
            
        return wallet

    async def get_transactions(self, wallet_id: uuid.UUID, skip: int = 0, limit: int = 50) -> Tuple[List[Transaction], int]:
        query = select(Transaction).where(Transaction.wallet_id == wallet_id).order_by(Transaction.created_at.desc())
        
        # Paginação manual ou usar tools do fastapi
        result = await self.db.execute(query.offset(skip).limit(limit))
        transactions = result.scalars().all()
        
        # Total
        from sqlalchemy import func
        count_query = select(func.count(Transaction.id)).where(Transaction.wallet_id == wallet_id)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(transactions), total

    async def add_transaction(self, wallet_id: uuid.UUID, type: TransactionType, amount: float, reference_id: str = None, description: str = None) -> Transaction:
        # Recuperar wallet atualizando os saldos
        query = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await self.db.execute(query)
        wallet = result.scalar_one_or_none()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet não encontrada")
            
        transaction = Transaction(
            wallet_id=wallet_id,
            type=type,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            reference_id=reference_id,
            description=description
        )
        
        if type == TransactionType.EARNING:
            wallet.available_balance += amount
            wallet.total_earned += amount
        elif type == TransactionType.PAYOUT:
            if wallet.available_balance < amount:
                raise HTTPException(status_code=400, detail="Saldo insuficiente")
            wallet.available_balance -= amount
        elif type == TransactionType.REFUND:
            wallet.available_balance -= amount
        elif type == TransactionType.FEE:
            wallet.available_balance -= amount
            
        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)
        
        return transaction
        
    async def request_payout(self, user_id: uuid.UUID, amount: float) -> Transaction:
        wallet = await self.get_or_create_wallet(user_id)
        
        if wallet.available_balance < amount:
            raise HTTPException(status_code=400, detail="Saldo disponível insuficiente para saque.")
            
        # Recuperar user para pegar o stripe account id
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user or not user.stripe_account_id:
            raise HTTPException(status_code=400, detail="Usuário não possui conta Stripe conectada para saque.")
            
        try:
            # Transferir fundos via Stripe Payout. 
            # A Stripe precisa ter o saldo retido ou enviamos do nosso balance.
            # Convertemos para centavos.
            payout = stripe.Payout.create(
                amount=int(amount * 100),
                currency="brl",
                stripe_account=user.stripe_account_id
            )
            
            # Registrar transação
            transaction = await self.add_transaction(
                wallet_id=wallet.id,
                type=TransactionType.PAYOUT,
                amount=amount,
                reference_id=payout.id,
                description="Saque para conta bancária via Stripe"
            )
            
            return transaction
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Erro no provedor de pagamento: {str(e)}")

    async def release_funds_to_available(self, booking_id: uuid.UUID) -> Transaction:
        """
        Libera os fundos de uma reserva para a carteira disponível do host.
        No Stripe Connect com Destination Charges, os fundos ficam na conta Stripe do Host
        como pendentes ou ficam na plataforma.
        Para representar no MVP, passamos do 'pending_balance' (se houvesse) ou apenas
        somamos no 'available_balance' do Host, registrando um EARNING.
        """
        from app.models.payment import Payment
        from app.models.booking import Booking
        from app.models.space import Space
        
        # Buscar o pagamento
        query = select(Payment).join(Booking).join(Space).where(Payment.booking_id == booking_id)
        result = await self.db.execute(query)
        payment = result.scalars().first()
        
        if not payment:
            raise ValueError(f"Pagamento não encontrado para booking {booking_id}")
            
        # Verificar idempotência
        tx_query = select(Transaction).where(Transaction.reference_id == f"booking_{booking_id}")
        tx_result = await self.db.execute(tx_query)
        if tx_result.scalars().first():
            raise ValueError(f"Fundos já liberados para booking {booking_id}")
            
        booking = await payment.awaitable_attrs.booking
        space = await booking.awaitable_attrs.space
        
        wallet = await self.get_or_create_wallet(space.host_id)
        
        # O valor a ser liberado é o host_amount (ou host_payout do booking)
        amount_to_release = float(booking.host_payout)
        
        # Registra a transação de ganho e soma no available_balance
        transaction = await self.add_transaction(
            wallet_id=wallet.id,
            type=TransactionType.EARNING,
            amount=amount_to_release,
            reference_id=f"booking_{booking_id}",
            description=f"Recebimento referente à reserva {booking_id}"
        )
        
        return transaction
