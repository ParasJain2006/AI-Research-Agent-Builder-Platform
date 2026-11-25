"""
agent_builder.graph.nodes.architecture_designer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Node that designs workflow nodes and directed edges for an agent definition.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

from langchain_core.messages import HumanMessage, SystemMessage

from shared.enums.status import AgentStatus
from shared.schemas.agent import AgentEdgeDefinition, AgentNodeDefinition
from agent_builder.graph.state import AgentBuilderState
from agent_builder.prompts.architecture_designer import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from agent_builder.services.llm_client import get_llm_client
from agent_builder.utils.json_parser import extract_json

logger = logging.getLogger(__name__)


async def architecture_designer_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Design workflow nodes and directed edges for the agent."""
    reqs = state.get("analyzed_requirements", {})
    request = state["build_request"]
    selected_tools = state.get("selected_tools", [])
    objective = reqs.get("objective") or request.objective
    capabilities = reqs.get("capabilities", [])

    user_prompt = USER_PROMPT_TEMPLATE.format(
        agent_name=request.agent_name,
        objective=objective,
        capabilities=", ".join(capabilities) if capabilities else "General assistance",
        selected_tools=", ".join(selected_tools) if selected_tools else "None",
    )

    try:
        llm = get_llm_client()
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parsed = extract_json(response.content)

        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object for architecture design, got {type(parsed).__name__}")

        raw_nodes = parsed.get("workflow_nodes") or []
        raw_edges = parsed.get("workflow_edges") or []
        entry_node = parsed.get("entry_node", "")

        # 1. Parse and validate workflow nodes
        nodes: List[AgentNodeDefinition] = []
        node_ids: Set[str] = set()

        for idx, node_data in enumerate(raw_nodes):
            if not isinstance(node_data, dict):
                continue
            raw_id = str(node_data.get("node_id") or f"node_{idx + 1}").strip().lower()
            # sanitize id
            node_id = "".join(c if c.isalnum() or c == "_" else "_" for c in raw_id)
            if not node_id or node_id in node_ids:
                node_id = f"node_{idx + 1}"
            node_ids.add(node_id)

            raw_allowed = node_data.get("allowed_tools") or []
            # Constrain to selected_tools only
            filtered_tools = [
                tool for tool in raw_allowed
                if isinstance(tool, str) and tool in selected_tools
            ]

            nodes.append(
                AgentNodeDefinition(
                    node_id=node_id,
                    node_type=str(node_data.get("node_type") or "task"),
                    description=str(node_data.get("description") or f"Execution step {node_id}"),
                    allowed_tools=filtered_tools,
                )
            )

        # Fallback if no nodes parsed
        if not nodes:
            entry_id = "initial_execution"
            nodes = [
                AgentNodeDefinition(
                    node_id=entry_id,
                    node_type="execution",
                    description="Processes incoming requests and executes tools",
                    allowed_tools=list(selected_tools),
                )
            ]
            node_ids = {entry_id}
            entry_node = entry_id

        # 2. Validate entry node
        if entry_node not in node_ids:
            entry_node = nodes[0].node_id

        # 3. Parse and validate workflow edges
        edges: List[AgentEdgeDefinition] = []
        for edge_data in raw_edges:
            if not isinstance(edge_data, dict):
                continue
            src = str(edge_data.get("source_node") or "").strip().lower()
            tgt = str(edge_data.get("target_node") or "").strip().lower()
            if src in node_ids and tgt in node_ids and src != tgt:
                edges.append(
                    AgentEdgeDefinition(
                        source_node=src,
                        target_node=tgt,
                        condition=edge_data.get("condition"),
                    )
                )

        # Ensure linear connectivity if nodes > 1 and edges are empty
        if len(nodes) > 1 and not edges:
            for i in range(len(nodes) - 1):
                edges.append(
                    AgentEdgeDefinition(
                        source_node=nodes[i].node_id,
                        target_node=nodes[i + 1].node_id,
                    )
                )

        logger.info(
            "Architecture designed: %d nodes, %d edges, entry=%s",
            len(nodes),
            len(edges),
            entry_node,
        )

        return {
            "proposed_nodes": nodes,
            "proposed_edges": edges,
            "entry_node": entry_node,
            "status": AgentStatus.DESIGNING,
        }

    except Exception as exc:
        err_msg = f"ARCHITECTURE_DESIGN_FAILED: {str(exc)}"
        logger.exception(err_msg)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "status": AgentStatus.FAILED,
        }
