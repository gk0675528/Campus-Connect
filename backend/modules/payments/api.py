"""Payment API Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.config.database import get_db
from core.dependencies.auth import get_current_user
from modules.payments.services.payment_service import PaymentService
from modules.payments.schemas import PaymentRequest, PaymentResponse
from modules.users.models import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create payment"""
    
    from modules.users.models import Session
    from sqlalchemy import select
    
    # Get session
    stmt = select(Session).where(Session.id == payment_data.session_id)
    session_result = await db.execute(stmt)
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the student can create this payment")
    
    payment = await PaymentService.create_payment(
        session_id=str(payment_data.session_id),
        amount=session.student_pays,
        platform_commission=session.student_pays * session.platform_commission_rate,
        mentor_amount=session.mentor_receives,
        payment_method=payment_data.payment_method,
        db=db
    )
    
    return payment


@router.post("/confirm/{payment_id}")
async def confirm_payment(
    payment_id: str,
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm payment completion"""
    
    payment = await PaymentService.get_payment(payment_id, db)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    from modules.users.models import Session
    session_result = await db.execute(select(Session).where(Session.id == payment.session_id))
    session = session_result.scalar_one_or_none()
    if not session or session.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    payment = await PaymentService.mark_payment_complete(
        payment_id=payment_id,
        transaction_id=transaction_id,
        db=db
    )
    
    return payment
