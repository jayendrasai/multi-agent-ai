import json
import logging
from collections.abc import Mapping
from typing import Any
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import EventType
from app.db.models import AgentEvent, TaskRun

logger = logging.getLogger(__name__)


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return json_safe(model_dump())
    return str(value)


async def append_event(
    session: AsyncSession,
    *,
    task_id: UUID,
    correlation_id: str,
    agent_name: str,
    event_type: EventType,
    payload: Mapping[str, Any],
    workflow_node_id: UUID | None = None,
) -> AgentEvent:
    task = await session.scalar(
        select(TaskRun).where(TaskRun.id == task_id).with_for_update()
    )
    if task is None:
        raise ValueError("Task run does not exist")

    task.event_sequence_counter += 1
    event = AgentEvent(
        task_run_id=task_id,
        workflow_node_id=workflow_node_id,
        agent_name=agent_name,
        event_type=event_type.value,
        payload=json_safe(payload),
        correlation_id=correlation_id,
        sequence_number=task.event_sequence_counter,
    )
    session.add(event)
    await session.flush()
    await _publish_event(event)
    return event


async def _publish_event(event: AgentEvent) -> None:
    """Publish workflow events without making Redis availability a workflow dependency."""
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.publish(
            f"task-events:{event.task_run_id}",
            json.dumps(
                {
                    "id": str(event.id),
                    "task_run_id": str(event.task_run_id),
                    "correlation_id": event.correlation_id,
                    "event_type": event.event_type,
                    "agent_name": event.agent_name,
                    "payload": event.payload,
                    "sequence_number": event.sequence_number,
                    "timestamp": event.created_at.isoformat(),
                }
            ),
        )
    except Exception:
        logger.exception(
            "Unable to publish workflow event",
            extra={"task_id": str(event.task_run_id)},
        )
    finally:
        await client.aclose()
