"""
agent_builder.tests.test_architecture_designer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the architecture_designer node.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from shared.enums.status import AgentStatus
from shared.schemas.agent import AgentBuildRequest
from agent_builder.graph.nodes.architecture_designer import architecture_designer_node
from agent_builder.graph.state import AgentBuilderState


def create_state() -> AgentBuilderState:
    return {
        "user_id": "usr_test",
        "request_id": "req_test",
        "session_id": "ses_test",
        "build_request": AgentBuildRequest(
            session_id="ses_test",
            agent_name="DocAnalyst",
            description="Analyzes uploaded documents",
            objective="Extract summaries and answers from PDFs",
        ),
        "analyzed_requirements": {
            "objective": "Extract summaries and answers from PDFs",
            "capabilities": ["Read uploaded files", "Synthesize responses"],
        },
        "selected_tools": ["document_reader"],
        "proposed_nodes": [],
        "proposed_edges": [],
        "entry_node": "",
        "generated_definition": None,
        "validation_errors": [],
        "refinement_count": 0,
        "status": AgentStatus.DESIGNING,
        "errors": [],
    }


@pytest.mark.asyncio
async def test_valid_architecture_designed():
    state = create_state()
    mock_payload = {
        "entry_node": "read_docs",
        "workflow_nodes": [
            {
                "node_id": "read_docs",
                "node_type": "reader",
                "description": "Reads document content",
                "allowed_tools": ["document_reader"],
            },
            {
                "node_id": "synthesize_answers",
                "node_type": "synthesizer",
                "description": "Synthesizes answers",
                "allowed_tools": [],
            },
        ],
        "workflow_edges": [
            {
                "source_node": "read_docs",
                "target_node": "synthesize_answers",
                "condition": None,
            }
        ],
    }
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps(mock_payload)))

    with patch("agent_builder.graph.nodes.architecture_designer.get_llm_client", return_value=mock_llm):
        result = await architecture_designer_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    assert result["entry_node"] == "read_docs"
    assert len(result["proposed_nodes"]) == 2
    assert len(result["proposed_edges"]) == 1
    assert result["proposed_nodes"][0].allowed_tools == ["document_reader"]


@pytest.mark.asyncio
async def test_node_tools_constrained_to_selected_tools():
    state = create_state()
    # selected_tools is ["document_reader"]. LLM tries to add "github_search" to a node.
    mock_payload = {
        "entry_node": "node_1",
        "workflow_nodes": [
            {
                "node_id": "node_1",
                "node_type": "reader",
                "description": "Reads docs",
                "allowed_tools": ["document_reader", "github_search"],
            }
        ],
        "workflow_edges": [],
    }
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=json.dumps(mock_payload)))

    with patch("agent_builder.graph.nodes.architecture_designer.get_llm_client", return_value=mock_llm):
        result = await architecture_designer_node(state)

    assert result["status"] == AgentStatus.DESIGNING
    # github_search should be filtered out from node allowed_tools
    assert result["proposed_nodes"][0].allowed_tools == ["document_reader"]
