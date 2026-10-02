import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.connection_manager import manager
from app.db.base import get_session
from app.auth.security import digest_session_token
from app.db.models import AgentEvent, Session, TaskRun
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str, db: AsyncSession = Depends(get_session)):
    try:
        task_uuid = UUID(task_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid task_id format")
        return

    session_token = websocket.cookies.get(get_settings().session_cookie_name)
    if not session_token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    auth_session = await db.scalar(
        select(Session).where(Session.token_digest == digest_session_token(session_token))
    )
    now = datetime.now(timezone.utc)
    if auth_session is None or auth_session.revoked_at is not None or auth_session.expires_at <= now:
        await websocket.close(code=1008, reason="Authentication required")
        return
    task = await db.scalar(
        select(TaskRun).where(TaskRun.id == task_uuid, TaskRun.user_id == auth_session.user_id)
    )
    if task is None:
        await websocket.close(code=1008, reason="Workflow not found")
        return
    auth_session.last_used_at = now
    await db.commit()

    await manager.connect(websocket, task_id)
    redis_client = redis.from_url(get_settings().redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task-events:{task_id}")
    try:
        stmt = select(AgentEvent).where(
            AgentEvent.task_run_id == task_uuid
        ).order_by(AgentEvent.sequence_number)
        result = await db.execute(stmt)
        for event in result.scalars().all():
            await websocket.send_json(_event_payload(event))

        while True:
            receive_task = asyncio.create_task(websocket.receive_text())
            message_task = asyncio.create_task(
                pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            )
            done, pending = await asyncio.wait(
                {receive_task, message_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for pending_task in pending:
                pending_task.cancel()

            if message_task in done:
                message = message_task.result()
                if message and message.get("data"):
                    await websocket.send_json(json.loads(message["data"]))
            if receive_task in done:
                data = receive_task.result()
                if data == "ping":
                    await websocket.send_text("pong")
            if not done:
                await websocket.send_text("ping")
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect(websocket, task_id)
    finally:
        await pubsub.aclose()
        await redis_client.aclose()


def _event_payload(event: AgentEvent) -> dict[str, object]:
    return {
        "id": str(event.id),
        "task_run_id": str(event.task_run_id),
        "correlation_id": event.correlation_id,
        "event_type": event.event_type,
        "agent_name": event.agent_name,
        "payload": event.payload,
        "sequence_number": event.sequence_number,
        "timestamp": event.created_at.isoformat(),
    }
