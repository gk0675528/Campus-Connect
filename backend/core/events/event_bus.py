"""Event Bus for Async Events"""

from typing import Callable, Dict, List
from core.config.logging import logger


class EventBus:
    """Simple event bus for async events"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to event"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.info(f"Subscribed to event: {event_type}")
    
    async def emit(self, event_type: str, data: dict):
        """Emit event"""
        if event_type not in self.subscribers:
            return
        
        logger.info(f"Emitting event: {event_type}")
        
        for handler in self.subscribers[event_type]:
            try:
                if hasattr(handler, '__call__'):
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {str(e)}")


# Global event bus instance
event_bus = EventBus()


# Event handlers
async def on_session_booked(data: dict):
    """Handle session booked event"""
    logger.info(f"Session booked: {data.get('session_id')}")


async def on_payment_completed(data: dict):
    """Handle payment completed event"""
    logger.info(f"Payment completed: {data.get('payment_id')}")


async def on_mentor_verified(data: dict):
    """Handle mentor verified event"""
    logger.info(f"Mentor verified: {data.get('user_id')}")


# Register event handlers
event_bus.subscribe("session_booked", on_session_booked)
event_bus.subscribe("payment_completed", on_payment_completed)
event_bus.subscribe("mentor_verified", on_mentor_verified)
