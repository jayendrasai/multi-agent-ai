from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.graph.agents.critic import critic_node, route_after_critic
from app.graph.agents.executor import analyst_node, researcher_node
from app.graph.agents.finalizer import (
    route_after_validator,
    synthesizer_node,
    validator_node,
)
from app.graph.agents.planner import planner_node
from app.graph.agents.router import route_after_router, router_node
from app.graph.state import AgentState

settings = get_settings()

def build_graph(checkpointer=None):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("router", router_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("validator", validator_node)

    # Set Entry Point
    workflow.set_entry_point("planner")

    # Add Edges
    workflow.add_edge("planner", "router")
    
    # Router Conditional Edges
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "researcher": "researcher",
            "analyst": "analyst",
            "synthesizer": "synthesizer"
        }
    )
    
    # Executors go to Critic
    workflow.add_edge("researcher", "critic")
    workflow.add_edge("analyst", "critic")
    
    # Critic Conditional Edges
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "router": "router",
            "researcher": "researcher",
            "analyst": "analyst"
        }
    )
    
    # Synthesizer goes to Validator
    workflow.add_edge("synthesizer", "validator")
    
    # Validator Conditional Edges
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "critic": "critic", # Loop back on failure
            "end": END
        }
    )

    # Checkpoint configuration
    # In a fully async env we would use AsyncPostgresSaver, but let's assume we initialize it appropriately later.
    # We will compile it without checkpointer for the time being as checkpointer instance needs a context manager.
    
    return workflow.compile(checkpointer=checkpointer)
