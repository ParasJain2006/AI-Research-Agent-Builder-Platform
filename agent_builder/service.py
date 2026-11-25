"""
agent_builder.service
~~~~~~~~~~~~~~~~~~~~~
Public service interface for the Agent Builder module.

Backend calls ONLY this module (build_agent, test_agent).
Contains no FastAPI/HTTP-specific code; communicates purely via Pydantic models
and ServiceContext.
"""

from __future__ import annotations

import logging
import uuid
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from shared.constants.tools import ALLOWED_TOOL_NAMES
from shared.enums.status import AgentStatus
from shared.exceptions.base import AgentGenerationFailed, InternalError
from shared.schemas.agent import (
    AgentBuildRequest,
    AgentDefinition,
    AgentTestRequest,
    AgentTestResult,
)
from shared.schemas.common import ServiceContext
from shared.utils.time import utc_now
from agent_builder.graph.graph import agent_builder_graph
from agent_builder.graph.nodes.validator import validate_agent_definition
from agent_builder.graph.state import AgentBuilderState
from agent_builder.services.llm_client import get_llm_client
from agent_builder.services.tool_registry import is_tool_allowed

logger = logging.getLogger(__name__)


async def build_agent(
    request: AgentBuildRequest,
    context: ServiceContext,
) -> AgentDefinition:
    """Build and validate an autonomous agent based on direct or research context.

    Parameters
    ----------
    request:
        The agent build specifications and constraints.
    context:
        Authenticated request metadata and execution parameters.

    Returns
    -------
    AgentDefinition:
        A validated, declarative AgentDefinition with status READY.

    Raises
    ------
    AgentGenerationFailed:
        If generation fails, tool selection is invalid, or refinement limits are exceeded.
    InternalError:
        If an unexpected system error occurs during workflow execution.
    """
    logger.info(
        "Starting build_agent for session=%s, agent_name=%s, request_id=%s",
        request.session_id,
        request.agent_name,
        context.request_id,
    )

    initial_state: AgentBuilderState = {
        "user_id": context.user_id,
        "request_id": context.request_id,
        "session_id": request.session_id,
        "build_request": request,
        "analyzed_requirements": {},
        "selected_tools": [],
        "proposed_nodes": [],
        "proposed_edges": [],
        "entry_node": "",
        "generated_definition": None,
        "validation_errors": [],
        "refinement_count": 0,
        "status": AgentStatus.DRAFT,
        "errors": [],
    }

    try:
        final_state = await agent_builder_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Unexpected error in agent_builder_graph execution: %s", exc)
        raise InternalError(f"Workflow execution failed: {str(exc)}") from exc

    status = final_state.get("status")
    definition = final_state.get("generated_definition")

    if status == AgentStatus.FAILED or definition is None:
        errors = final_state.get("errors", []) + final_state.get("validation_errors", [])
        err_detail = "; ".join(errors) if errors else "Agent build workflow completed with status FAILED."
        logger.error("build_agent failed for request_id=%s: %s", context.request_id, err_detail)
        raise AgentGenerationFailed(err_detail)

    logger.info(
        "build_agent completed successfully: agent_id=%s, tools=%s",
        definition.agent_id,
        definition.tools,
    )
    return definition


async def test_agent(
    agent: AgentDefinition,
    request: AgentTestRequest,
    context: ServiceContext,
) -> AgentTestResult:
    """Perform a controlled test run of an AgentDefinition.

    Executes a dry-run against the agent's system prompt and approved tools
    using the LLM. Does NOT execute arbitrary or unverified Python/shell code.

    Parameters
    ----------
    agent:
        The validated AgentDefinition under test.
    request:
        The test input text and optional test context dictionary.
    context:
        Authenticated request metadata and execution parameters.

    Returns
    -------
    AgentTestResult:
        Details of execution success, trace, and response output.
    """
    test_id = f"test_{uuid.uuid4().hex[:12]}"
    started_at = utc_now()
    trace: List[str] = []
    errors: List[str] = []

    logger.info(
        "Starting test_agent: test_id=%s, agent_id=%s, request_id=%s",
        test_id,
        agent.agent_id,
        context.request_id,
    )

    try:
        # 1. Complete deterministic validation reusing central validator logic
        trace.append(f"1. Performing complete deterministic validation for '{agent.agent_name}' ({agent.agent_id})")
        validation_errors = validate_agent_definition(agent)
        if validation_errors:
            errors.extend(validation_errors)
            trace.append(f"FAILED validation: {validation_errors}")
            return AgentTestResult(
                test_id=test_id,
                agent_id=agent.agent_id,
                success=False,
                output=None,
                errors=errors,
                execution_trace=trace,
                started_at=started_at,
                completed_at=utc_now(),
            )

        trace.append(f"2. Verified approved tools: {agent.tools}")
        trace.append(f"3. Verified entry node: '{agent.entry_node}' and workflow nodes: {[n.node_id for n in agent.workflow_nodes]}")

        # 2. Build controlled execution prompt
        trace.append("4. Preparing controlled test harness prompt")
        tools_summary = ", ".join(agent.tools) if agent.tools else "none"
        test_system_prompt = (
            f"{agent.system_prompt}\n\n"
            f"[TEST HARNESS CONTEXT]\n"
            f"- Available Tools: {tools_summary}\n"
            f"- Entry Node: {agent.entry_node}\n"
            f"- Mode: Controlled Dry-Run Test (do not fabricate citations, do not attempt unauthorized network calls)"
        )

        user_content = request.input_text
        if request.test_context:
            user_content += f"\n\nContext: {request.test_context}"

        # 3. Controlled LLM invocation
        trace.append("5. Invoking LLM in controlled test mode")
        llm = get_llm_client(
            provider=context.llm_provider,
            model=context.llm_model,
        )

        response = await llm.ainvoke([
            SystemMessage(content=test_system_prompt),
            HumanMessage(content=user_content),
        ])

        output_str = str(response.content)
        trace.append("6. Received response from controlled test run")
        completed_at = utc_now()

        logger.info("test_agent completed successfully: test_id=%s", test_id)
        return AgentTestResult(
            test_id=test_id,
            agent_id=agent.agent_id,
            success=True,
            output=output_str,
            errors=[],
            execution_trace=trace,
            started_at=started_at,
            completed_at=completed_at,
        )

    except Exception as exc:
        logger.exception("test_agent failed with error: %s", exc)
        errors.append(f"TEST_EXECUTION_ERROR: {str(exc)}")
        trace.append(f"ERROR: {str(exc)}")
        return AgentTestResult(
            test_id=test_id,
            agent_id=agent.agent_id,
            success=False,
            output=None,
            errors=errors,
            execution_trace=trace,
            started_at=started_at,
            completed_at=utc_now(),
        )
