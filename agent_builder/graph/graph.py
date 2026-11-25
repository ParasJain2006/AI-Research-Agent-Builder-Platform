"""
agent_builder.graph.graph
~~~~~~~~~~~~~~~~~~~~~~~~~
Assembles and compiles the Agent Builder LangGraph StateGraph.

Pipeline flow:
requirement_analyzer -> tool_selector -> architecture_designer -> agent_generator
  -> validator -> (refiner -> validator loop if errors and count < 3) -> END
"""

from __future__ import annotations

import logging
from langgraph.graph import END, StateGraph

from shared.enums.status import AgentStatus
from agent_builder.graph.nodes.agent_generator import agent_generator_node
from agent_builder.graph.nodes.architecture_designer import architecture_designer_node
from agent_builder.graph.nodes.refiner import refiner_node
from agent_builder.graph.nodes.requirement_analyzer import requirement_analyzer_node
from agent_builder.graph.nodes.tool_selector import tool_selector_node
from agent_builder.graph.nodes.validator import validator_node
from agent_builder.graph.state import AgentBuilderState

logger = logging.getLogger(__name__)

MAX_REFINEMENT_ATTEMPTS = 3


def should_continue(state: AgentBuilderState) -> str:
    """Check if state is failed; if so abort to END, otherwise continue."""
    if state.get("status") == AgentStatus.FAILED:
        return "end"
    return "continue"


def route_after_validator(state: AgentBuilderState) -> str:
    """Route after validator: to refiner if fixable errors remain, else END."""
    status = state.get("status")
    if status == AgentStatus.READY:
        return "end"
    if status == AgentStatus.FAILED:
        return "end"

    validation_errors = state.get("validation_errors", [])
    refinement_count = state.get("refinement_count", 0)

    if validation_errors and refinement_count < MAX_REFINEMENT_ATTEMPTS:
        return "refine"
    return "end"


def route_after_refiner(state: AgentBuilderState) -> str:
    """Route after refiner back to validator, or abort if failed."""
    if state.get("status") == AgentStatus.FAILED:
        return "end"
    return "validator"


def create_agent_builder_graph() -> StateGraph:
    """Assemble and compile the StateGraph for the Agent Builder pipeline."""
    workflow = StateGraph(AgentBuilderState)

    # 1. Register nodes
    workflow.add_node("requirement_analyzer", requirement_analyzer_node)
    workflow.add_node("tool_selector", tool_selector_node)
    workflow.add_node("architecture_designer", architecture_designer_node)
    workflow.add_node("agent_generator", agent_generator_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("refiner", refiner_node)

    # 2. Set entry point
    workflow.set_entry_point("requirement_analyzer")

    # 3. requirement_analyzer -> tool_selector
    workflow.add_conditional_edges(
        "requirement_analyzer",
        should_continue,
        {"continue": "tool_selector", "end": END},
    )

    # 4. tool_selector -> architecture_designer
    workflow.add_conditional_edges(
        "tool_selector",
        should_continue,
        {"continue": "architecture_designer", "end": END},
    )

    # 5. architecture_designer -> agent_generator
    workflow.add_conditional_edges(
        "architecture_designer",
        should_continue,
        {"continue": "agent_generator", "end": END},
    )

    # 6. agent_generator -> validator
    workflow.add_edge("agent_generator", "validator")

    # 7. validator -> refiner or END
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {"refine": "refiner", "end": END},
    )

    # 8. refiner -> validator or END
    workflow.add_conditional_edges(
        "refiner",
        route_after_refiner,
        {"validator": "validator", "end": END},
    )

    return workflow.compile()


# Module-level compiled graph
agent_builder_graph = create_agent_builder_graph()
