"""Razorpay Payment Client"""

from core.config.settings import settings
import razorpay
import asyncio
from core.config.logging import logger


client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class RazorpayClient:
    """Razorpay Payment Integration"""
    
    @staticmethod
    async def create_order(amount: float, currency: str = "INR", metadata: dict = None) -> dict:
        """Create payment order (runs in thread)"""
        try:
            loop = asyncio.get_event_loop()

            def _create():
                return client.order.create({
                    "amount": int(amount * 100),  # Convert to paise
                    "currency": currency,
                    "notes": metadata or {}
                })

            order = await loop.run_in_executor(None, _create)

            logger.info(f"Order created: {order['id']}")
            return {
                "order_id": order["id"],
                "amount": order["amount"] / 100,
                "currency": order["currency"]
            }

        except Exception as e:
            logger.error(f"Razorpay error: {str(e)}")
            raise
    
    @staticmethod
    async def verify_payment(payment_id: str, order_id: str, signature: str) -> bool:
        """Verify payment signature (runs verification in thread)"""
        try:
            loop = asyncio.get_event_loop()

            def _verify():
                return client.utility.verify_payment_signature({
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature
                })

            # The SDK raises on failure; if it returns without exception, treat as verified
            await loop.run_in_executor(None, _verify)

            logger.info(f"Payment verified: {payment_id}")
            return True

        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return False
    
    @staticmethod
    async def capture_payment(payment_id: str, amount: float) -> dict:
        """Capture payment (runs in thread)"""
        try:
            loop = asyncio.get_event_loop()

            def _capture():
                return client.payment.capture(payment_id, int(amount * 100))

            capture = await loop.run_in_executor(None, _capture)

            logger.info(f"Payment captured: {payment_id}")
            return {
                "payment_id": capture.get("id") or capture.get("payment_id") or payment_id,
                "status": capture.get("status"),
                "amount": capture.get("amount", 0) / 100
            }

        except Exception as e:
            logger.error(f"Capture error: {str(e)}")
            raise
