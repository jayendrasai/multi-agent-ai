from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.models import (
    AgentEvent,
    ErrorLog,
    ExecutionMetrics,
    TaskRun,
    ToolInvocation,
    WorkflowNode,
)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: UUID) -> ModelType | None:
        return await self.session.get(self.model, id)

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj


class TaskRunRepository(BaseRepository[TaskRun]):
    def __init__(self, session: AsyncSession):
        super().__init__(TaskRun, session)

    async def get_by_correlation_id(self, correlation_id: str) -> TaskRun | None:
        stmt = select(self.model).where(self.model.correlation_id == correlation_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()


class WorkflowNodeRepository(BaseRepository[WorkflowNode]):
    def __init__(self, session: AsyncSession):
        super().__init__(WorkflowNode, session)

    async def get_by_task_run(self, task_run_id: UUID) -> Sequence[WorkflowNode]:
        stmt = select(self.model).where(self.model.task_run_id == task_run_id).order_by(self.model.created_at)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class AgentEventRepository(BaseRepository[AgentEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(AgentEvent, session)

    async def get_latest_sequence(self, task_run_id: UUID) -> int:
        stmt = select(self.model.sequence_number).where(
            self.model.task_run_id == task_run_id
        ).order_by(self.model.sequence_number.desc()).limit(1)
        result = await self.session.execute(stmt)
        seq = result.scalar()
        return seq if seq is not None else 0


class ToolInvocationRepository(BaseRepository[ToolInvocation]):
    def __init__(self, session: AsyncSession):
        super().__init__(ToolInvocation, session)


class ErrorLogRepository(BaseRepository[ErrorLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErrorLog, session)


class ExecutionMetricsRepository(BaseRepository[ExecutionMetrics]):
    def __init__(self, session: AsyncSession):
        super().__init__(ExecutionMetrics, session)
