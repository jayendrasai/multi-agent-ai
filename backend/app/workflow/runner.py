import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select

from app.core.config import get_settings
from app.core.constants import EventType
from app.db.base import async_session_maker
from app.db.models import TaskRun, WorkflowNode
from app.graph.builder import build_graph
from app.graph.state import AgentState
from app.workflow.events import append_event, json_safe
from app.workflow.cache import set_cached_result

logger = logging.getLogger(__name__)


def _checkpoint_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def execute_workflow(task_id: UUID) -> dict[str, str]:
    settings = get_settings()
    async with async_session_maker() as session:
        task = await session.scalar(select(TaskRun).where(TaskRun.id == task_id))
        if task is None:
            raise ValueError("Task run does not exist")

        task.status = "RUNNING"
        await append_event(
            session,
            task_id=task.id,
            correlation_id=task.correlation_id,
            agent_name="System",
            event_type=EventType.NODE_STARTED,
            payload={
                "node_name": "workflow",
                "node_type": "workflow",
                "status": "RUNNING",
                "input": task.prompt,
            },
        )
        await session.commit()

        initial_state: AgentState = {
            "task_run_id": str(task.id),
            "correlation_id": task.correlation_id,
            "input_prompt": task.prompt,
            "messages": [],
            "plan": [],
            "current_step_id": None,
            "active_agent": "Planner",
            "final_output": None,
            "iteration_count": 0,
            "feedback_loops": 0,
            "validation_loops": 0,
            "errors": [],
        }
        config = {
            "configurable": {"thread_id": str(task.id)},
            "recursion_limit": settings.max_graph_iterations,
        }

        node_ids: dict[str, UUID] = {}
        try:
            async with AsyncPostgresSaver.from_conn_string(
                _checkpoint_url(settings.database_url)
            ) as checkpointer:
                await checkpointer.setup()
                graph = build_graph(checkpointer=checkpointer)
                final_state: dict = {}
                async for debug_event in graph.astream(
                    initial_state, config=config, stream_mode="debug"
                ):
                    await _persist_debug_event(
                        session, task, debug_event, node_ids
                    )
                    if debug_event.get("type") == "task_result":
                        for write in debug_event["payload"].get("result", []):
                            if write and write[0] == "__root__":
                                final_state.update(write[1])
                    await session.commit()

                saved_state = await graph.aget_state(config)
                final_state = saved_state.values or final_state

            task.final_result = final_state.get("final_output")
            task.status = "COMPLETED"
            task.completed_at = datetime.now(timezone.utc)
            await append_event(
                session,
                task_id=task.id,
                correlation_id=task.correlation_id,
                agent_name="System",
                event_type=EventType.WORKFLOW_COMPLETED,
                payload={"status": task.status},
            )
            await session.commit()
            if task.user_id is not None and task.final_result:
                await set_cached_result(task.user_id, task.prompt, task.final_result)
            return {"task_id": str(task.id), "status": task.status}
        except Exception:
            logger.exception("Workflow execution failed", extra={"task_id": str(task.id)})
            task.status = "FAILED"
            await append_event(
                session,
                task_id=task.id,
                correlation_id=task.correlation_id,
                agent_name="System",
                event_type=EventType.WORKFLOW_FAILED,
                payload={"status": task.status, "message": "Workflow execution failed"},
            )
            await session.commit()
            raise


async def _persist_debug_event(
    session,
    task: TaskRun,
    debug_event: dict,
    node_ids: dict[str, UUID],
) -> None:
    event_type = debug_event.get("type")
    payload = debug_event.get("payload", {})
    node_name = payload.get("name", "workflow")
    if event_type == "task":
        node = WorkflowNode(
            task_run_id=task.id,
            node_type="agent",
            node_name=node_name,
            status="RUNNING",
            inputs=json_safe(payload.get("input")),
            started_at=datetime.now(timezone.utc),
        )
        session.add(node)
        await session.flush()
        node_ids[payload["id"]] = node.id
        await append_event(
            session,
            task_id=task.id,
            correlation_id=task.correlation_id,
            agent_name=node_name,
            event_type=EventType.NODE_STARTED,
            payload={
                "node_id": str(node.id),
                "node_name": node.node_name,
                "node_type": node.node_type,
                "status": node.status,
                "input": node.inputs,
            },
            workflow_node_id=node.id,
        )
    elif event_type == "task_result":
        node_id = node_ids.get(payload.get("id"))
        if node_id is None:
            return
        node = await session.get(WorkflowNode, node_id)
        if node is None:
            return
        node.status = "COMPLETED"
        node.outputs = json_safe(payload.get("result"))
        node.completed_at = datetime.now(timezone.utc)
        node.execution_duration_ms = int(
            (node.completed_at - node.started_at).total_seconds() * 1000
        ) if node.started_at else None
        await append_event(
            session,
            task_id=task.id,
            correlation_id=task.correlation_id,
            agent_name=node.node_name,
            event_type=EventType.NODE_COMPLETED,
            payload={
                "node_id": str(node.id),
                "node_name": node.node_name,
                "node_type": node.node_type,
                "status": node.status,
                "input": node.inputs,
                "output": node.outputs,
                "duration_ms": node.execution_duration_ms,
                "retries": node.retry_count,
            },
            workflow_node_id=node.id,
        )
