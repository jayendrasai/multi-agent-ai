import logging
from typing import Any

from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def router_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Router Agent executing")
    
    plan = state.get("plan", [])
    
    # Find the first pending step
    for step in plan:
        if step["status"] == "PENDING":
            assigned_agent = step.get("assigned_agent", "Researcher")
            logger.info(f"Routing to {assigned_agent} for step: {step['step_id']}")
            return {
                "active_agent": assigned_agent,
                "current_step_id": step["step_id"],
                "iteration_count": state.get("iteration_count", 0) + 1
            }
            
    # If all steps are complete, go to Synthesizer
    logger.info("All steps completed. Routing to Synthesizer.")
    return {
        "active_agent": "Synthesizer",
        "current_step_id": None,
        "iteration_count": state.get("iteration_count", 0) + 1
    }


def route_after_router(state: AgentState) -> str:
    """Conditional edge from Router to next agent."""
    active_agent = state.get("active_agent")
    if active_agent == "Researcher":
        return "researcher"
    elif active_agent == "Analyst":
        return "analyst"
    else:
        return "synthesizer"
