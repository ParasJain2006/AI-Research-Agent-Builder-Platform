"""
agent_builder.graph.nodes.requirement_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Node that analyzes build requests and produces structured requirements.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from shared.enums.status import AgentStatus
from agent_builder.graph.state import AgentBuilderState
from agent_builder.prompts.requirement_analyzer import (
    RESEARCH_CONTEXT_TEMPLATE,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from agent_builder.services.llm_client import get_llm_client
from agent_builder.utils.json_parser import extract_json

logger = logging.getLogger(__name__)


async def requirement_analyzer_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Analyze the AgentBuildRequest and extract structured requirements."""
    request = state["build_request"]
    logger.info("Analyzing requirements for agent_name=%s", request.agent_name)

    # 1. Format research context section if present
    research_context_section = ""
    if request.research_context is not None:
        rc = request.research_context
        findings_str = "\n  - " + "\n  - ".join(rc.key_findings) if rc.key_findings else "None"
        research_context_section = RESEARCH_CONTEXT_TEMPLATE.format(
            research_summary=rc.research_summary or "None",
            key_findings=findings_str,
            recommended_approach=rc.recommended_approach or "Not specified",
        )

    # 2. Format user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(
        agent_name=request.agent_name,
        description=request.description,
        objective=request.objective,
        suggested_tools=request.required_tools or "None",
        constraints=request.constraints or "None",
        research_context_section=research_context_section,
    )

    try:
        llm = get_llm_client()
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parsed = extract_json(response.content)

        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object from requirement analyzer, got {type(parsed).__name__}")

        # Ensure required keys exist with sensible fallbacks
        analyzed = {
            "objective": str(parsed.get("objective") or request.objective),
            "capabilities": list(parsed.get("capabilities") or [request.description]),
            "constraints": list(parsed.get("constraints") or request.constraints),
            "suggested_tools": list(parsed.get("suggested_tools") or request.required_tools),
        }

        logger.info("Requirement analysis complete for %s", request.agent_name)
        return {
            "analyzed_requirements": analyzed,
            "status": AgentStatus.ANALYZING,
        }

    except Exception as exc:
        err_msg = f"REQUIREMENT_ANALYSIS_FAILED: {str(exc)}"
        logger.exception(err_msg)
        return {
            "errors": state.get("errors", []) + [err_msg],
            "status": AgentStatus.FAILED,
        }
