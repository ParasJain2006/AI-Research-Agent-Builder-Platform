"""
agent_builder.graph.nodes.validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deterministic validation node for generated agent definitions.

Performs strict structural, schema, and security checks without LLM calls:
1. Pydantic schema validity.
2. Approved tool names (against ALLOWED_TOOL_NAMES).
3. Valid entry node reference.
4. Valid source and target node references for all edges.
5. Graph connectivity from entry node.
6. Non-empty system prompt (> 10 characters).
7. Refinement limit enforcement (maximum 3 attempts).
"""

from __future__ import annotations

import collections
import logging
from typing import Any, Dict, List, Set

from shared.constants.tools import ALLOWED_TOOL_NAMES
from shared.enums.status import AgentStatus
from shared.schemas.agent import AgentDefinition
from agent_builder.graph.state import AgentBuilderState
from agent_builder.services.tool_registry import is_tool_allowed

logger = logging.getLogger(__name__)

MAX_REFINEMENT_ATTEMPTS = 3


def validate_agent_definition(raw_definition: Any) -> List[str]:
    """Deterministically validate an AgentDefinition against all structural,
    schema, and policy constraints.

    Can be called directly by service layers (e.g. test_agent) or from the graph.

    Returns
    -------
    List[str]
        List of validation error strings. Empty if definition is valid.
    """
    errors: List[str] = []

    if raw_definition is None:
        return ["MISSING_DEFINITION: No AgentDefinition was provided for validation."]

    definition: AgentDefinition
    if isinstance(raw_definition, AgentDefinition):
        definition = raw_definition
    elif isinstance(raw_definition, dict):
        try:
            definition = AgentDefinition.model_validate(raw_definition)
        except Exception as exc:
            return [f"SCHEMA_VALIDATION_ERROR: {str(exc)}"]
    else:
        return [f"SCHEMA_VALIDATION_ERROR: Invalid definition type {type(raw_definition).__name__}."]

    # 1. Approved tool names
    for tool_name in definition.tools:
        if tool_name not in ALLOWED_TOOL_NAMES or not is_tool_allowed(tool_name):
            errors.append(f"TOOL_NOT_ALLOWED: Tool '{tool_name}' is not in the approved tool registry.")

    # 2. Node-level allowed_tools checks
    node_ids: Set[str] = {node.node_id for node in definition.workflow_nodes}
    for node in definition.workflow_nodes:
        for tool_name in node.allowed_tools:
            if tool_name not in ALLOWED_TOOL_NAMES or not is_tool_allowed(tool_name):
                errors.append(
                    f"TOOL_NOT_ALLOWED: Node '{node.node_id}' permits unapproved tool '{tool_name}'."
                )
            if tool_name not in definition.tools:
                errors.append(
                    f"INVALID_NODE_TOOL: Node '{node.node_id}' specifies tool '{tool_name}' "
                    f"which is not declared in global agent tools."
                )

    # 3. Valid entry node
    if not definition.entry_node or definition.entry_node not in node_ids:
        errors.append(
            f"INVALID_ENTRY_NODE: Entry node '{definition.entry_node}' does not exist in workflow_nodes."
        )

    # 4. Valid source and target node references in edges
    for edge in definition.workflow_edges:
        if edge.source_node not in node_ids:
            errors.append(
                f"INVALID_EDGE_SOURCE: Edge source_node '{edge.source_node}' does not exist in workflow_nodes."
            )
        if edge.target_node not in node_ids:
            errors.append(
                f"INVALID_EDGE_TARGET: Edge target_node '{edge.target_node}' does not exist in workflow_nodes."
            )

    # 5. Graph connectivity (all nodes must be reachable from entry_node)
    if definition.entry_node in node_ids and len(node_ids) > 1:
        adjacency: Dict[str, List[str]] = collections.defaultdict(list)
        for edge in definition.workflow_edges:
            adjacency[edge.source_node].append(edge.target_node)

        visited: Set[str] = set()
        queue = collections.deque([definition.entry_node])
        while queue:
            curr = queue.popleft()
            if curr not in visited:
                visited.add(curr)
                for neighbor in adjacency[curr]:
                    if neighbor not in visited and neighbor in node_ids:
                        queue.append(neighbor)

        unreachable = node_ids - visited
        if unreachable:
            errors.append(
                f"GRAPH_CONNECTIVITY_ERROR: Unreachable nodes from entry '{definition.entry_node}': "
                f"{sorted(unreachable)}."
            )

    # 6. Non-empty system prompt
    if not definition.system_prompt or len(definition.system_prompt.strip()) < 10:
        errors.append("EMPTY_SYSTEM_PROMPT: System prompt must be non-empty and at least 10 characters.")

    return errors


async def validator_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Validate the generated AgentDefinition deterministically in the LangGraph workflow."""
    raw_definition = state.get("generated_definition")
    refinement_count = state.get("refinement_count", 0)

    if raw_definition is None:
        errors = ["MISSING_DEFINITION: No AgentDefinition was generated."]
        return {
            "validation_errors": errors,
            "status": AgentStatus.FAILED,
            "errors": state.get("errors", []) + errors,
        }

    errors = validate_agent_definition(raw_definition)

    definition: AgentDefinition
    if isinstance(raw_definition, AgentDefinition):
        definition = raw_definition
    else:
        definition = AgentDefinition.model_validate(raw_definition)

    # Refinement limit check
    if errors:
        if refinement_count >= MAX_REFINEMENT_ATTEMPTS:
            errors.append(
                f"REFINEMENT_LIMIT_EXCEEDED: Maximum refinement attempts ({MAX_REFINEMENT_ATTEMPTS}) reached."
            )
            final_status = AgentStatus.FAILED
            definition_copy = definition.model_copy(update={"status": AgentStatus.FAILED})
        else:
            final_status = AgentStatus.VALIDATING
            definition_copy = definition.model_copy(update={"status": AgentStatus.VALIDATING})

        logger.warning(
            "Validator found %d errors (refinement_count=%d)",
            len(errors),
            refinement_count,
            extra={"validation_errors": errors},
        )
        return {
            "validation_errors": errors,
            "status": final_status,
            "generated_definition": definition_copy,
            "errors": state.get("errors", []) + (errors if final_status == AgentStatus.FAILED else []),
        }

    # Success
    ready_definition = definition.model_copy(update={"status": AgentStatus.READY})
    logger.info("Validator passed successfully for agent_id=%s", definition.agent_id)
    return {
        "validation_errors": [],
        "status": AgentStatus.READY,
        "generated_definition": ready_definition,
    }
