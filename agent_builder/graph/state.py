"""
agent_builder.graph.state
~~~~~~~~~~~~~~~~~~~~~~~~~
Typed state schema for the Agent Builder LangGraph workflow.

Conforms to Contract §12.1.  All nodes in the agent-builder graph read from
and write updates to this state dictionary.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from shared.enums.status import AgentStatus
from shared.schemas.agent import (
    AgentBuildRequest,
    AgentDefinition,
    AgentEdgeDefinition,
    AgentNodeDefinition,
)


class AgentBuilderState(TypedDict):
    """LangGraph state schema for the agent-builder pipeline."""

    user_id: str
    request_id: str
    session_id: str
    build_request: AgentBuildRequest
    analyzed_requirements: Dict[str, Any]
    selected_tools: List[str]
    proposed_nodes: List[AgentNodeDefinition]
    proposed_edges: List[AgentEdgeDefinition]
    entry_node: str
    generated_definition: Optional[AgentDefinition]
    validation_errors: List[str]
    refinement_count: int
    status: AgentStatus
    errors: List[str]
