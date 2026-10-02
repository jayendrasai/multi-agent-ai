import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.graph.llm import configured_llm
from app.graph.state import AgentPlan, AgentState
from app.tools.local import run_analysis, run_calculator
from app.tools.search import run_search
from app.tools.weather import run_weather

logger = logging.getLogger(__name__)
settings = get_settings()

llm = configured_llm()

RESEARCHER_PROMPT = """You are the Researcher Agent.
Your task is to execute the current step using your tools (search, weather).
Respond with the findings."""

ANALYST_PROMPT = """You are the Analyst Agent.
Your task is to execute the current step using your tools (analysis, calculator, formatter).
Respond with the processed result."""


def _get_current_step(state: AgentState) -> AgentPlan | None:
    current_step_id = state.get("current_step_id")
    for step in state.get("plan", []):
        if step["step_id"] == current_step_id:
            return step
    return None


def researcher_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Researcher Agent executing")
    step = _get_current_step(state)
    if not step:
        return {"errors": ["Researcher: No active step found"]}
        
    try:
        if "weather" in step["description"].lower():
            result = run_weather({"location": "San Francisco"})
        else:
            result = run_search({"query": step["description"], "num_results": 3})
            
        messages = [
            SystemMessage(content=RESEARCHER_PROMPT),
            HumanMessage(content=f"Task: {step['description']}\nTool Result: {result}")
        ]
        
        response = llm.invoke(messages)
        
        return {
            "messages": [response],
            "active_agent": "Researcher",
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    except Exception as e:
        logger.error(f"Researcher failed: {e}")
        return {"errors": [str(e)]}


def analyst_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Analyst Agent executing")
    step = _get_current_step(state)
    if not step:
        return {"errors": ["Analyst: No active step found"]}
        
    try:
        # Similarly, routing to a tool based on basic logic
        if "calculate" in step["description"].lower():
            result = run_calculator({"expression": "2+2"})
        else:
            result = run_analysis({"data": step["description"], "analysis_type": "summary"})
            
        messages = [
            SystemMessage(content=ANALYST_PROMPT),
            HumanMessage(content=f"Task: {step['description']}\nTool Result: {result}")
        ]
        
        response = llm.invoke(messages)
        
        return {
            "messages": [response],
            "active_agent": "Analyst",
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    except Exception as e:
        logger.error(f"Analyst failed: {e}")
        return {"errors": [str(e)]}
