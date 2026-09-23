"""Payment Service"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.users.models import Payment, Session as SessionModel, Wallet
from core.config.constants import PaymentStatus
from core.exceptions.auth_exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Payment Processing Service"""

    @staticmethod
    async def get_payment(payment_id: str, db: AsyncSession) -> Payment:
        result = await db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_payment(
        session_id: str,
        amount: float,
        platform_commission: float,
        mentor_amount: float,
        payment_method: str,
        db: AsyncSession
    ) -> Payment:
        """Create payment"""
        
        # Validate session
        session_stmt = select(SessionModel).where(SessionModel.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise NotFoundError("Session not found")
        
        payment = Payment(
            session_id=session_id,
            amount=amount,
            platform_commission=platform_commission,
            mentor_amount=mentor_amount,
            payment_method=payment_method,
            status=PaymentStatus.PENDING
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        
        logger.info(f"Payment created: {payment.id}")
        return payment
    
    @staticmethod
    async def mark_payment_complete(
        payment_id: str,
        transaction_id: str,
        db: AsyncSession
    ) -> Payment:
        """Mark payment as complete"""
        
        payment_stmt = select(Payment).where(Payment.id == payment_id)
        payment_result = await db.execute(payment_stmt)
        payment = payment_result.scalar_one_or_none()
        
        if not payment:
            raise NotFoundError("Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            if payment.transaction_id != transaction_id:
                raise ValidationError("Payment is already completed")
            return payment
        
        payment.status = PaymentStatus.COMPLETED
        payment.transaction_id = transaction_id
        
        # Add to mentor's wallet
        session_stmt = select(SessionModel).where(SessionModel.id == payment.session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
        
        if session:
            wallet_stmt = select(Wallet).where(Wallet.user_id == session.mentor_id)
            wallet_result = await db.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()
            
            if wallet:
                wallet.balance += payment.mentor_amount
                wallet.total_earned += payment.mentor_amount
        
        await db.commit()
        await db.refresh(payment)
        
        logger.info(f"Payment completed: {payment_id}")
        return payment
