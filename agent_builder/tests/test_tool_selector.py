"""
agent_builder.tests.test_tool_selector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the tool_selector node with mocked LLM responses.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from shared.enums.status import AgentStatus
from shared.schemas.agent import AgentBuildRequest
from agent_builder.graph.nodes.tool_selector import tool_selector_node
from agent_builder.graph.state import AgentBuilderState


def create_mock_state(
    objective: str = "Search for research papers and synthesize findings",
    required_tools: list[str] = None,
    suggested_tools: list[str] = None,
) -> AgentBuilderState:
    return {
        "user_id": "usr_123",
        "request_id": "req_123",
        "session_id": "ses_123",
        "build_request": AgentBuildRequest(
            session_id="ses_123",
            agent_name="TestAgent",
            description="Test agent description",
            objective=objective,
            required_tools=required_tools or [],
        ),
        "analyzed_requirements": {
            "objective": objective,
            "capabilities": ["search papers", "summarize content"],
            "suggested_tools": suggested_tools or [],
        },
        "selected_tools": [],
        "proposed_nodes": [],
        "proposed_edges": [],
        "entry_node": "",
        "generated_definition": None,
        "validation_errors": [],
        "refinement_count": 0,
        "status": AgentStatus.ANALYZING,
        "errors": [],
    }


@pytest.mark.asyncio
async def test_valid_tools_selected():
    state = create_mock_state()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(["paper_search", "web_search"]))
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert "paper_search" in result["selected_tools"]
    assert "web_search" in result["selected_tools"]


@pytest.mark.asyncio
async def test_unknown_tool_filtered_out():
    state = create_mock_state()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(
            content=json.dumps(["github_search", "arbitrary_unsafe_exec", "documentation_search"])
        )
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert "github_search" in result["selected_tools"]
    assert "documentation_search" in result["selected_tools"]
    assert "arbitrary_unsafe_exec" not in result["selected_tools"]


@pytest.mark.asyncio
async def test_all_unknown_tools_causes_failure():
    state = create_mock_state()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(["bash_shell", "python_interpreter"]))
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.FAILED
    assert any("TOOL_NOT_ALLOWED" in err for err in result["errors"])
    assert result["selected_tools"] == []


@pytest.mark.asyncio
async def test_required_tools_included():
    state = create_mock_state(required_tools=["document_reader"])
    mock_llm = MagicMock()
    # LLM recommends web_search, user requested document_reader
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(["web_search"]))
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert "document_reader" in result["selected_tools"]
    assert "web_search" in result["selected_tools"]


@pytest.mark.asyncio
async def test_developer_agent_tool_selection():
    """Validates use case 2: GitHub / Developer Agent."""
    state = create_mock_state(objective="Search GitHub repositories and documentation to compare tech stacks")
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(
            content=json.dumps(["github_search", "documentation_search", "web_search"])
        )
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert set(result["selected_tools"]) == {"github_search", "documentation_search", "web_search"}


@pytest.mark.asyncio
async def test_document_analysis_agent_tool_selection():
    """Validates use case 3: Document Analysis Agent."""
    state = create_mock_state(
        objective="Read uploaded research PDFs and answer user questions",
        required_tools=["document_reader"],
    )
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(["document_reader"]))
    )

    with patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm):
        result = await tool_selector_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert result["selected_tools"] == ["document_reader"]
