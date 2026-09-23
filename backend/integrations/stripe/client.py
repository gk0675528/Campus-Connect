"""Stripe Payment Client"""

from core.config.settings import settings
import stripe
import asyncio
from core.config.logging import logger


stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeClient:
    """Stripe Payment Integration"""
    
    @staticmethod
    async def create_payment_intent(amount: float, currency: str = "usd", metadata: dict = None) -> dict:
        """Create payment intent (runs Stripe SDK in a thread to avoid blocking the event loop)"""
        try:
            loop = asyncio.get_event_loop()

            def _create():
                return stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Convert to cents
                    currency=currency,
                    metadata=metadata or {}
                )

            intent = await loop.run_in_executor(None, _create)

            logger.info(f"Payment intent created: {intent.id}")
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
            }

        except Exception as e:
            logger.error(f"Stripe error: {str(e)}")
            raise
    
    @staticmethod
    async def confirm_payment(payment_intent_id: str) -> dict:
        """Confirm payment (retrieve intent without blocking the event loop)"""
        try:
            loop = asyncio.get_event_loop()

            def _retrieve():
                return stripe.PaymentIntent.retrieve(payment_intent_id)

            intent = await loop.run_in_executor(None, _retrieve)

            return {
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert from cents
                "currency": intent.currency
            }

        except Exception as e:
            logger.error(f"Stripe error: {str(e)}")
            raise
    
    @staticmethod
    async def create_refund(payment_intent_id: str, amount: float = None) -> dict:
        """Create refund (runs in thread)"""
        try:
            refund_params = {"payment_intent": payment_intent_id}
            if amount:
                refund_params["amount"] = int(amount * 100)

            loop = asyncio.get_event_loop()

            def _refund():
                return stripe.Refund.create(**refund_params)

            refund = await loop.run_in_executor(None, _refund)

            logger.info(f"Refund created: {refund.id}")
            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100
            }

        except Exception as e:
            logger.error(f"Stripe refund error: {str(e)}")
            raise
