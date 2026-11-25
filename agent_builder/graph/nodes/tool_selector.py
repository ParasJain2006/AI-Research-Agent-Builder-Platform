"""
agent_builder.graph.nodes.tool_selector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Node that selects approved tools based on analyzed agent requirements.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from shared.constants.tools import ALLOWED_TOOL_NAMES
from shared.enums.status import AgentStatus
from agent_builder.graph.state import AgentBuilderState
from agent_builder.prompts.tool_selector import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agent_builder.services.llm_client import get_llm_client
from agent_builder.services.tool_registry import is_tool_allowed, list_allowed_tools
from agent_builder.utils.json_parser import extract_json

logger = logging.getLogger(__name__)


async def tool_selector_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Select appropriate tools strictly from the approved tool registry."""
    reqs = state.get("analyzed_requirements", {})
    request = state["build_request"]
    objective = reqs.get("objective") or request.objective
    capabilities = reqs.get("capabilities", [])

    # Collect suggested hints
    hint_tools = list(request.required_tools or [])
    for t in reqs.get("suggested_tools", []):
        if t not in hint_tools:
            hint_tools.append(t)

    allowed_list = list_allowed_tools()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        objective=objective,
        capabilities=", ".join(capabilities) if capabilities else "General assistance",
        requested_tools=", ".join(hint_tools) if hint_tools else "None",
        allowed_tools=", ".join(allowed_list),
    )

    try:
        llm = get_llm_client()
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parsed = extract_json(response.content)

        raw_candidates: List[str] = []
        if isinstance(parsed, list):
            raw_candidates = [str(item) for item in parsed]
        elif isinstance(parsed, dict):
            # In case LLM returns {"tools": [...]}
            raw_tools = parsed.get("tools") or parsed.get("selected_tools") or []
            raw_candidates = [str(t) for t in raw_tools]

        # Strict filtering against approved tool whitelist
        selected: List[str] = []
        for cand in raw_candidates:
            cand_clean = cand.strip().lower()
            if cand_clean in ALLOWED_TOOL_NAMES and is_tool_allowed(cand_clean):
                if cand_clean not in selected:
                    selected.append(cand_clean)

        # Also incorporate any approved tools specifically requested by the user
        for req_tool in hint_tools:
            req_clean = req_tool.strip().lower()
            if req_clean in ALLOWED_TOOL_NAMES and is_tool_allowed(req_clean):
                if req_clean not in selected:
                    selected.append(req_clean)

        # Guardrail: Must have at least one valid tool
        if not selected:
            err_msg = (
                f"TOOL_NOT_ALLOWED: No approved tools could be selected. "
                f"Candidates were {raw_candidates}, none match whitelist {sorted(ALLOWED_TOOL_NAMES)}."
            )
            logger.error(err_msg)
            return {
                "selected_tools": [],
                "errors": state.get("errors", []) + [err_msg],
                "status": AgentStatus.FAILED,
            }

        logger.info("Selected approved tools: %s", selected)
        return {
            "selected_tools": selected,
            "status": AgentStatus.DESIGNING,
        }

    except Exception as exc:
        err_msg = f"TOOL_SELECTION_FAILED: {str(exc)}"
        logger.exception(err_msg)
        return {
            "selected_tools": [],
            "errors": state.get("errors", []) + [err_msg],
            "status": AgentStatus.FAILED,
        }
