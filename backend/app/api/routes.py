import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import EventResponse, TaskCreate, TaskResponse, WorkflowNodeResponse
from app.auth.dependencies import get_current_user
from app.db.base import get_session
from app.db.models import AgentEvent, TaskRun, User, WorkflowNode
from app.worker import run_workflow_task
from app.workflow.cache import get_cached_result

router = APIRouter()

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    request: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    correlation_id = f"corr-{uuid.uuid4().hex[:8]}"
    
    new_task = TaskRun(
        user_id=user.id,
        correlation_id=correlation_id,
        status="PENDING",
        prompt=request.prompt,
    )
    db.add(new_task)
    cached_result = await get_cached_result(user.id, request.prompt)
    if cached_result is not None:
        new_task.status = "COMPLETED"
        new_task.final_result = cached_result
        new_task.completed_at = datetime.now(timezone.utc)
        await db.flush()
        from app.core.constants import EventType
        from app.workflow.events import append_event

        await append_event(
            db,
            task_id=new_task.id,
            correlation_id=new_task.correlation_id,
            agent_name="System",
            event_type=EventType.WORKFLOW_COMPLETED,
            payload={"status": "COMPLETED", "cache_hit": True},
        )
        await db.commit()
        await db.refresh(new_task)
        return new_task

    await db.commit()
    await db.refresh(new_task)
    
    try:
        run_workflow_task.delay(str(new_task.id))
    except Exception:
        new_task.status = "FAILED"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workflow service is temporarily unavailable. Please try again.",
        )
    
    return new_task


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(TaskRun).where(TaskRun.user_id == user.id).order_by(TaskRun.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    stmt = select(TaskRun).where(TaskRun.id == task_id, TaskRun.user_id == user.id)
    result = await db.execute(stmt)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task


async def _require_task(task_id: uuid.UUID, user: User, db: AsyncSession) -> TaskRun:
    task = await db.scalar(
        select(TaskRun).where(TaskRun.id == task_id, TaskRun.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/tasks/{task_id}/events", response_model=list[EventResponse])
async def list_task_events(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await _require_task(task_id, user, db)
    stmt = (
        select(AgentEvent)
        .where(AgentEvent.task_run_id == task_id)
        .order_by(AgentEvent.sequence_number.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tasks/{task_id}/nodes", response_model=list[WorkflowNodeResponse])
async def list_task_nodes(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await _require_task(task_id, user, db)
    stmt = (
        select(WorkflowNode)
        .where(WorkflowNode.task_run_id == task_id)
        .order_by(WorkflowNode.created_at.asc(), WorkflowNode.id.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/history", response_model=list[TaskResponse])
async def history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    run_status: str | None = Query(default=None, alias="status", max_length=20),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    stmt = (
        select(TaskRun)
        .where(TaskRun.user_id == user.id)
        .order_by(TaskRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if run_status:
        stmt = stmt.where(TaskRun.status == run_status.upper())
    result = await db.execute(stmt)
    return result.scalars().all()
