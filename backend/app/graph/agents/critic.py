import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.graph.llm import configured_llm
from app.graph.state import AgentState

logger = logging.getLogger(__name__)
settings = get_settings()

llm = configured_llm()

CRITIC_PROMPT = """You are the Critic Agent.
Evaluate the result of the last executed step.
Does it satisfy the requirements of the step description?
Respond with 'PASS' if it is acceptable, or 'FAIL: <reason>' if it is not."""

def critic_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Critic Agent executing")
    
    last_message = state["messages"][-1].content if state.get("messages") else ""
    
    messages = [
        SystemMessage(content=CRITIC_PROMPT),
        HumanMessage(content=f"Last output: {last_message}")
    ]
    
    response = llm.invoke(messages)
    evaluation = response.content.strip()
    
    current_step_id = state.get("current_step_id")
    plan = state.get("plan", [])
    updated_plan = []
    passed = evaluation.startswith("PASS")
    
    for step in plan:
        if step["step_id"] == current_step_id:
            updated_step = step.copy()
            if passed:
                updated_step["status"] = "COMPLETED"
                updated_step["result"] = last_message
            else:
                updated_step["status"] = "FAILED"
                updated_step["result"] = evaluation
            updated_plan.append(updated_step)
        else:
            updated_plan.append(step)
            
    if passed:
        logger.info("Critic passed the step.")
        return {
            "plan": updated_plan,
            "active_agent": "Critic", # will be routed next
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    else:
        logger.warning(f"Critic failed the step: {evaluation}")
        return {
            "plan": updated_plan,
            "feedback_loops": state.get("feedback_loops", 0) + 1,
            "errors": [f"Critic Failure: {evaluation}"],
            "active_agent": "Critic",
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def route_after_critic(state: AgentState) -> str:
    """Conditional edge from Critic."""
    if state.get("feedback_loops", 0) >= settings.max_feedback_loops:
        return "router" # Forced continue or fail
        
    current_step_id = state.get("current_step_id")
    for step in state.get("plan", []):
        if step["step_id"] == current_step_id:
            if step["status"] == "COMPLETED":
                return "router"
            else:
                # Need to retry
                return step.get("assigned_agent", "researcher").lower()
    return "router"
