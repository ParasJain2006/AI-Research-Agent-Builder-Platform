"""
agent_builder.tests.test_refiner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the refiner node.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from shared.enums.status import AgentStatus
from shared.schemas.agent import (
    AgentBuildRequest,
    AgentDefinition,
    AgentEdgeDefinition,
    AgentNodeDefinition,
)
from agent_builder.graph.nodes.refiner import refiner_node
from agent_builder.graph.state import AgentBuilderState


def create_state(
    refinement_count: int = 0,
    errors: list[str] = None,
    definition: AgentDefinition | None = None,
) -> AgentBuilderState:
    if definition is None:
        definition = AgentDefinition(
            agent_id="agt_test123",
            agent_name="TestBot",
            description="Test agent",
            objective="Do things",
            system_prompt="Initial short prompt",
            tools=["web_search"],
            workflow_nodes=[
                AgentNodeDefinition(
                    node_id="main",
                    node_type="task",
                    description="Main task",
                    allowed_tools=["web_search"],
                )
            ],
            workflow_edges=[],
            entry_node="main",
            status=AgentStatus.GENERATING,
            created_at="2026-11-15T00:00:00Z",
            updated_at="2026-11-15T00:00:00Z",
        )
    return {
        "user_id": "usr_test",
        "request_id": "req_test",
        "session_id": "ses_test",
        "build_request": AgentBuildRequest(
            session_id="ses_test",
            agent_name="TestBot",
            description="Test agent",
            objective="Do things",
        ),
        "analyzed_requirements": {},
        "selected_tools": ["web_search"],
        "proposed_nodes": [],
        "proposed_edges": [],
        "entry_node": "main",
        "generated_definition": definition,
        "validation_errors": errors or ["EMPTY_SYSTEM_PROMPT: Prompt too short."],
        "refinement_count": refinement_count,
        "status": AgentStatus.VALIDATING,
        "errors": [],
    }


@pytest.mark.asyncio
async def test_refinement_increments_count_and_updates_prompt():
    state = create_state(refinement_count=0)
    mock_llm = MagicMock()
    refined_prompt = "You are TestBot. Thoroughly search the web and produce rigorous answers."
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps({"system_prompt": refined_prompt}))
    )

    with patch("agent_builder.graph.nodes.refiner.get_llm_client", return_value=mock_llm):
        result = await refiner_node(state)

    assert result["refinement_count"] == 1
    assert result["status"] == AgentStatus.VALIDATING
    assert result["validation_errors"] == []
    assert result["generated_definition"].system_prompt == refined_prompt


@pytest.mark.asyncio
async def test_refinement_bounded_at_3():
    # Attempting a 4th refinement should fail immediately
    state = create_state(refinement_count=3)

    result = await refiner_node(state)

    assert result["refinement_count"] == 4
    assert result["status"] == AgentStatus.FAILED
    assert any("REFINEMENT_LIMIT_EXCEEDED" in err for err in result["errors"])


@pytest.mark.asyncio
async def test_refinement_without_definition_fails_gracefully():
    state = create_state(definition=False)
    state["generated_definition"] = None

    result = await refiner_node(state)

    assert result["status"] == AgentStatus.FAILED
    assert any("REFINEMENT_FAILED" in err for err in result["errors"])
