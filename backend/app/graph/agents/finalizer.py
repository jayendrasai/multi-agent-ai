import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.config import get_settings
from app.graph.llm import configured_llm
from app.graph.state import AgentState

logger = logging.getLogger(__name__)
settings = get_settings()

llm = configured_llm()

SYNTHESIZER_PROMPT = """You are the Synthesizer Agent.
Given the original prompt and the completed plan with results, synthesize a comprehensive final response.
"""

VALIDATOR_PROMPT = """You are the Validator Agent.
Review the synthesized final output against the original user prompt.
Does it answer the prompt accurately and completely?
Respond with 'PASS' if it is acceptable, or 'FAIL: <reason>' if it is not."""


def synthesizer_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Synthesizer Agent executing")
    
    plan_context = ""
    for step in state.get("plan", []):
        plan_context += f"Step: {step['description']}\nResult: {step.get('result', '')}\n\n"
        
    messages = [
        SystemMessage(content=SYNTHESIZER_PROMPT),
        HumanMessage(content=f"Original Prompt: {state['input_prompt']}\n\nExecution Results:\n{plan_context}")
    ]
    
    response = llm.invoke(messages)
    
    return {
        "final_output": response.content,
        "active_agent": "Synthesizer",
        "iteration_count": state.get("iteration_count", 0) + 1
    }


def validator_node(state: AgentState) -> dict[str, Any]:
    logger.info(f"[{state['correlation_id']}] Validator Agent executing")
    
    messages = [
        SystemMessage(content=VALIDATOR_PROMPT),
        HumanMessage(content=f"Original Prompt: {state['input_prompt']}\n\nSynthesized Output: {state.get('final_output')}")
    ]
    
    response = llm.invoke(messages)
    evaluation = response.content.strip()
    
    passed = evaluation.startswith("PASS")
    
    if passed:
        logger.info("Validator passed the final output.")
        return {
            "active_agent": "Validator",
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    else:
        logger.warning(f"Validator failed the final output: {evaluation}")
        return {
            "validation_loops": state.get("validation_loops", 0) + 1,
            "errors": [f"Validation Failure: {evaluation}"],
            "active_agent": "Validator",
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def route_after_validator(state: AgentState) -> str:
    """Conditional edge from Validator."""
    if state.get("validation_loops", 0) >= settings.max_validation_loops:
        return "end" # Forced end
        
    # If the last message in errors is a validation failure, we need to go back
    if state.get("errors") and "Validation Failure" in state["errors"][-1]:
        return "critic" # or router to re-plan, we send to critic for re-evaluation of last step for simplicity
    
    return "end"
