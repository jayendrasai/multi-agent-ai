from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.constants import EventType
from app.db.base import async_session_maker
from app.db.models import TaskRun
from app.workflow.events import append_event


async def mark_stale_workflows_failed() -> int:
    """Close jobs orphaned by a worker crash so the UI never waits forever."""
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.workflow_stale_timeout)
    async with async_session_maker() as session:
        result = await session.execute(
            select(TaskRun).where(
                TaskRun.status.in_(("PENDING", "RUNNING")),
                TaskRun.updated_at < cutoff,
            ).with_for_update()
        )
        stale_tasks = result.scalars().all()
        for task in stale_tasks:
            task.status = "FAILED"
            await append_event(
                session,
                task_id=task.id,
                correlation_id=task.correlation_id,
                agent_name="System",
                event_type=EventType.WORKFLOW_FAILED,
                payload={"status": "FAILED", "message": "Workflow interrupted; retry is required."},
            )
        await session.commit()
        return len(stale_tasks)
