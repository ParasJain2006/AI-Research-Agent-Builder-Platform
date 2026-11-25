"""
agent_builder.graph.nodes.agent_generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Node that generates the complete AgentDefinition and system prompt.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from shared.enums.status import AgentStatus
from shared.schemas.agent import AgentDefinition
from shared.utils.time import utc_now
from agent_builder.graph.state import AgentBuilderState
from agent_builder.prompts.agent_generator import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agent_builder.services.llm_client import get_llm_client
from agent_builder.utils.json_parser import extract_json

logger = logging.getLogger(__name__)


async def agent_generator_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Assemble the complete AgentDefinition and generate its production system prompt."""
    request = state["build_request"]
    reqs = state.get("analyzed_requirements", {})
    selected_tools = state.get("selected_tools", [])
    proposed_nodes = state.get("proposed_nodes", [])
    proposed_edges = state.get("proposed_edges", [])
    entry_node = state.get("entry_node", "")

    objective = reqs.get("objective") or request.objective
    capabilities = reqs.get("capabilities", [])
    constraints = reqs.get("constraints") or request.constraints

    nodes_summary = ", ".join(f"{n.node_id} ({n.node_type})" for n in proposed_nodes)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        agent_name=request.agent_name,
        objective=objective,
        description=request.description,
        capabilities=", ".join(capabilities) if capabilities else "General assistance",
        constraints=", ".join(constraints) if constraints else "Standard safety and reliability",
        selected_tools=", ".join(selected_tools) if selected_tools else "None",
        workflow_nodes=nodes_summary or "Default workflow",
    )

    system_prompt_str = ""
    try:
        llm = get_llm_client()
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parsed = extract_json(response.content)
        if isinstance(parsed, dict) and "system_prompt" in parsed:
            system_prompt_str = str(parsed["system_prompt"]).strip()
    except Exception as exc:
        logger.warning("LLM system prompt generation failed: %s; using deterministic fallback", exc)

    # Robust deterministic fallback if LLM returned empty prompt or failed
    if not system_prompt_str or len(system_prompt_str) < 10:
        tool_desc = ", ".join(selected_tools) if selected_tools else "none"
        system_prompt_str = (
            f"You are {request.agent_name}, an autonomous agent specialized in {request.description}.\n\n"
            f"Objective: {objective}\n"
            f"Allowed Tools: {tool_desc}\n\n"
            f"Guidelines:\n"
            f"1. Use only your approved tools to gather information.\n"
            f"2. Cite your sources accurately and report limitations transparently.\n"
            f"3. Never execute unverified code or commands."
        )

    now_iso = utc_now()
    agent_id = f"agt_{uuid.uuid4().hex[:12]}"

    definition = AgentDefinition(
        agent_id=agent_id,
        agent_name=request.agent_name,
        description=request.description,
        objective=objective,
        system_prompt=system_prompt_str,
        tools=list(selected_tools),
        workflow_nodes=list(proposed_nodes),
        workflow_edges=list(proposed_edges),
        entry_node=entry_node or (proposed_nodes[0].node_id if proposed_nodes else "entry"),
        constraints=list(constraints),
        status=AgentStatus.GENERATING,
        schema_version="1.0",
        created_at=now_iso,
        updated_at=now_iso,
    )

    logger.info("Agent definition generated: agent_id=%s, tools=%s", agent_id, selected_tools)

    return {
        "generated_definition": definition,
        "status": AgentStatus.GENERATING,
    }
