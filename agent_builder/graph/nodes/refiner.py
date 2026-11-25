"""
agent_builder.graph.nodes.refiner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Node that applies targeted refinements to an AgentDefinition based on validation feedback.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from shared.enums.status import AgentStatus
from shared.utils.time import utc_now
from agent_builder.graph.state import AgentBuilderState
from agent_builder.prompts.refiner import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agent_builder.services.llm_client import get_llm_client
from agent_builder.utils.json_parser import extract_json

logger = logging.getLogger(__name__)


async def refiner_node(state: AgentBuilderState) -> Dict[str, Any]:
    """Refine the AgentDefinition based on validation errors."""
    definition = state.get("generated_definition")
    current_count = state.get("refinement_count", 0) + 1
    errors = state.get("validation_errors", [])

    logger.info(
        "Refining agent definition (attempt %d/3) for errors: %s",
        current_count,
        errors,
    )

    if definition is None:
        return {
            "refinement_count": current_count,
            "status": AgentStatus.FAILED,
            "errors": state.get("errors", []) + ["REFINEMENT_FAILED: No definition exists to refine."],
        }

    # Bounded refinement: Fail if exceeding limit
    if current_count > 3:
        err_msg = "REFINEMENT_LIMIT_EXCEEDED: Maximum refinement attempts (3) exceeded."
        logger.error(err_msg)
        return {
            "refinement_count": current_count,
            "status": AgentStatus.FAILED,
            "errors": state.get("errors", []) + [err_msg],
        }

    user_prompt = USER_PROMPT_TEMPLATE.format(
        agent_name=definition.agent_name,
        objective=definition.objective,
        system_prompt=definition.system_prompt,
        validation_errors="; ".join(errors),
        refinement_instruction="Address the validation errors while preserving the agent's core purpose.",
    )

    refined_prompt = definition.system_prompt
    try:
        llm = get_llm_client()
        response = await llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parsed = extract_json(response.content)
        if isinstance(parsed, dict) and "system_prompt" in parsed:
            cand = str(parsed["system_prompt"]).strip()
            if len(cand) >= 10:
                refined_prompt = cand
    except Exception as exc:
        logger.warning("LLM refinement invocation failed: %s; keeping existing definition", exc)

    updated_definition = definition.model_copy(
        update={
            "system_prompt": refined_prompt,
            "updated_at": utc_now(),
            "status": AgentStatus.VALIDATING,
        }
    )

    return {
        "generated_definition": updated_definition,
        "refinement_count": current_count,
        "validation_errors": [],  # Clear so validator can run clean checks
        "status": AgentStatus.VALIDATING,
    }
