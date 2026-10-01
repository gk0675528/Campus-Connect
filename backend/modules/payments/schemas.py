"""Payment Schemas"""

from pydantic import BaseModel
from typing import Literal
from datetime import datetime
import uuid


class PaymentRequest(BaseModel):
    """Create payment request"""
    session_id: uuid.UUID
    payment_method: Literal["stripe", "razorpay"]


class PaymentResponse(BaseModel):
    """Payment response"""
    id: uuid.UUID
    session_id: uuid.UUID
    amount: float
    platform_commission: float
    mentor_amount: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    """Wallet response"""
    id: uuid.UUID
    user_id: uuid.UUID
    balance: float
    total_earned: float
    total_spent: float
    
    class Config:
        from_attributes = True
