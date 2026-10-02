import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.llm import configured_llm
from app.graph.state import AgentPlan, AgentState

logger = logging.getLogger(__name__)
llm = configured_llm()

PLANNER_PROMPT = """You are the Planner Agent for an AI Orchestration system.
Your job is to break down the user's prompt into a logical step-by-step plan.
The system has two executor agents you can assign tasks to:
1. 'Researcher' - for gathering information (search, weather).
2. 'Analyst' - for processing data, calculating, or formatting.

Respond ONLY with a JSON object in this format:
{
    "plan": [
        {
            "step_id": "step_1",
            "description": "Detailed description of the step",
            "assigned_agent": "Researcher" | "Analyst"
        }
    ]
}
"""

def planner_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Planner Agent executing")
    
    messages = [
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=state["input_prompt"])
    ]
    
    response = llm.invoke(messages)
    
    try:
        # Strip markdown code blocks if present
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        parsed_plan = json.loads(content)
        plan = []
        for step in parsed_plan.get("plan", []):
            plan.append(AgentPlan(
                step_id=step["step_id"],
                description=step["description"],
                assigned_agent=step["assigned_agent"],
                status="PENDING",
                result=None
            ))
            
        return {
            "plan": plan,
            "active_agent": "Planner",
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    except Exception as e:
        logger.error(f"Planner failed to generate valid JSON plan: {e}")
        return {
            "errors": [f"Planner Error: {e!s}"],
            "active_agent": "Planner",
            "iteration_count": state.get("iteration_count", 0) + 1
        }
