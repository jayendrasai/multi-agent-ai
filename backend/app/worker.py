import asyncio
import logging
from uuid import UUID

from celery import Celery
from celery.signals import worker_ready

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "orchestrator_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tools.search", "app.tools.weather", "app.tools.local"],
)

_worker_loop: asyncio.AbstractEventLoop | None = None


def _run_workflow(coro):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coro)


@worker_ready.connect
def recover_orphaned_workflows(**_kwargs) -> None:
    from app.workflow.recovery import mark_stale_workflows_failed

    recovered = _run_workflow(mark_stale_workflows_failed())
    if recovered:
        logger.info("Marked stale workflows as failed", extra={"count": recovered})

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(
    bind=True,
    name="orchestrator.run_workflow",
    soft_time_limit=settings.celery_task_soft_time_limit,
    time_limit=settings.celery_task_time_limit,
)
def run_workflow_task(self, task_id: str) -> dict[str, str]:
    from app.workflow.runner import execute_workflow

    return _run_workflow(execute_workflow(UUID(task_id)))
