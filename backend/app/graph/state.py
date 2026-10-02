import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentPlan(TypedDict):
    step_id: str
    description: str
    assigned_agent: str
    status: str
    result: str | None


class AgentState(TypedDict):
    task_run_id: str
    correlation_id: str
    input_prompt: str
    messages: Annotated[list[BaseMessage], operator.add]
    plan: list[AgentPlan]
    current_step_id: str | None
    active_agent: str
    final_output: str | None
    iteration_count: int
    feedback_loops: int
    validation_loops: int
    errors: Annotated[list[str], operator.add]
