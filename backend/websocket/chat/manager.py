"""WebSocket Chat Manager"""

from fastapi import WebSocket
from typing import Dict, List, Set
from core.config.logging import logger


class ConnectionManager:
    """Manage WebSocket connections with per-room locking and safe removal of broken sockets"""

    def __init__(self):
        # Room -> Set of WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Room -> asyncio.Lock to protect modifications per room
        self._locks: Dict[str, "asyncio.Lock"] = {}

    async def _get_lock(self, room_id: str):
        import asyncio
        if room_id not in self._locks:
            self._locks[room_id] = asyncio.Lock()
        return self._locks[room_id]

    async def connect(self, room_id: str, websocket: WebSocket):
        """Accept and store connection"""
        await websocket.accept()

        lock = await self._get_lock(room_id)
        async with lock:
            if room_id not in self.active_connections:
                self.active_connections[room_id] = set()
            self.active_connections[room_id].add(websocket)

        logger.info(f"Client connected to room {room_id}")

    async def disconnect(self, room_id: str, websocket: WebSocket):
        """Remove connection safely"""
        if room_id not in self.active_connections:
            logger.info(f"Client disconnect called for unknown room {room_id}")
            return

        lock = await self._get_lock(room_id)
        async with lock:
            self.active_connections[room_id].discard(websocket)
            if len(self.active_connections[room_id]) == 0:
                # cleanup
                del self.active_connections[room_id]
                if room_id in self._locks:
                    del self._locks[room_id]

        logger.info(f"Client disconnected from room {room_id}")

    async def broadcast(self, room_id: str, message: dict):
        """Broadcast message to all clients in room. Removes dead connections."""
        if room_id not in self.active_connections:
            return

        # make a shallow copy to avoid mutation during iteration
        connections = list(self.active_connections[room_id])
        lock = await self._get_lock(room_id)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message to a client in {room_id}: {str(e)}")
                # Remove broken connection under lock
                async with lock:
                    if room_id in self.active_connections:
                        self.active_connections[room_id].discard(connection)
                        if len(self.active_connections[room_id]) == 0:
                            del self.active_connections[room_id]
                            if room_id in self._locks:
                                del self._locks[room_id]

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send personal message with error handling"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            # Best-effort close
            try:
                await websocket.close()
            except Exception:
                pass


# Global connection manager
manager = ConnectionManager()
