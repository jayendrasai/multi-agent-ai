import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # task_id -> set of WebSockets
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            # We create a list to avoid dictionary changed size during iteration
            connections = list(self.active_connections[task_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending to websocket for task {task_id}: {e}")
                    self.disconnect(connection, task_id)


manager = ConnectionManager()
