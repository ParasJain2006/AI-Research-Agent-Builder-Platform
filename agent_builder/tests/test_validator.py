"""
agent_builder.tests.test_validator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the deterministic validator node.
"""

from __future__ import annotations

import pytest

from shared.enums.status import AgentStatus
from shared.schemas.agent import (
    AgentBuildRequest,
    AgentDefinition,
    AgentEdgeDefinition,
    AgentNodeDefinition,
)
from agent_builder.graph.nodes.validator import validator_node
from agent_builder.graph.state import AgentBuilderState


def create_sample_definition(
    tools: list[str] = None,
    entry_node: str = "node_1",
    nodes: list[AgentNodeDefinition] = None,
    edges: list[AgentEdgeDefinition] = None,
    system_prompt: str = "You are a professional research agent specializing in CS literature.",
    status: AgentStatus = AgentStatus.GENERATING,
) -> AgentDefinition:
    if tools is None:
        tools = ["web_search", "paper_search"]
    if nodes is None:
        nodes = [
            AgentNodeDefinition(
                node_id="node_1",
                node_type="search",
                description="Search for papers and web documents",
                allowed_tools=["web_search", "paper_search"],
            ),
            AgentNodeDefinition(
                node_id="node_2",
                node_type="summarize",
                description="Summarize collected evidence",
                allowed_tools=[],
            ),
        ]
    if edges is None:
        edges = [
            AgentEdgeDefinition(
                source_node="node_1",
                target_node="node_2",
            )
        ]
    return AgentDefinition(
        agent_id="agt_12345678",
        agent_name="ResearchAssistant",
        description="Assists in academic paper discovery and synthesis",
        objective="Find relevant papers on distributed systems and summarize findings",
        system_prompt=system_prompt,
        tools=tools,
        workflow_nodes=nodes,
        workflow_edges=edges,
        entry_node=entry_node,
        constraints=["Do not fabricate citations"],
        status=status,
        created_at="2026-11-15T00:00:00Z",
        updated_at="2026-11-15T00:00:00Z",
    )


def create_state(
    definition: AgentDefinition | None = None,
    refinement_count: int = 0,
) -> AgentBuilderState:
    return {
        "user_id": "usr_test123",
        "request_id": "req_test123",
        "session_id": "ses_test123",
        "build_request": AgentBuildRequest(
            session_id="ses_test123",
            agent_name="ResearchAssistant",
            description="Test description",
            objective="Test objective",
        ),
        "analyzed_requirements": {},
        "selected_tools": ["web_search", "paper_search"],
        "proposed_nodes": [],
        "proposed_edges": [],
        "entry_node": "node_1",
        "generated_definition": definition,
        "validation_errors": [],
        "refinement_count": refinement_count,
        "status": AgentStatus.GENERATING,
        "errors": [],
    }


@pytest.mark.asyncio
async def test_valid_definition_passes():
    definition = create_sample_definition()
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.READY
    assert result["validation_errors"] == []
    assert result["generated_definition"].status == AgentStatus.READY


@pytest.mark.asyncio
async def test_unknown_tool_rejected():
    definition = create_sample_definition(tools=["web_search", "unauthorized_tool"])
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("unauthorized_tool" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_missing_entry_node_caught():
    definition = create_sample_definition(entry_node="non_existent_node")
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("INVALID_ENTRY_NODE" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_broken_edge_caught():
    broken_edges = [
        AgentEdgeDefinition(source_node="node_1", target_node="ghost_target")
    ]
    definition = create_sample_definition(edges=broken_edges)
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("INVALID_EDGE_TARGET" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_graph_unreachable_node_caught():
    nodes = [
        AgentNodeDefinition(
            node_id="node_1",
            node_type="search",
            description="Entry search",
            allowed_tools=["web_search"],
        ),
        AgentNodeDefinition(
            node_id="node_2",
            node_type="isolated",
            description="Isolated island node",
            allowed_tools=[],
        ),
    ]
    edges = []  # No edge from node_1 to node_2
    definition = create_sample_definition(nodes=nodes, edges=edges)
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("GRAPH_CONNECTIVITY_ERROR" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_empty_system_prompt_caught():
    definition = create_sample_definition(system_prompt="   ")
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("EMPTY_SYSTEM_PROMPT" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_node_tool_not_in_global_tools():
    nodes = [
        AgentNodeDefinition(
            node_id="node_1",
            node_type="search",
            description="Node uses github_search",
            allowed_tools=["github_search"],  # Not in agent's tools!
        ),
    ]
    definition = create_sample_definition(
        tools=["web_search"],
        nodes=nodes,
        edges=[],
    )
    state = create_state(definition=definition, refinement_count=0)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.VALIDATING
    assert any("INVALID_NODE_TOOL" in err for err in result["validation_errors"])


@pytest.mark.asyncio
async def test_refinement_limit_enforced():
    definition = create_sample_definition(tools=["web_search", "unauthorized_tool"])
    # refinement_count = 3 means 3 attempts were already made, so validator fails terminal
    state = create_state(definition=definition, refinement_count=3)
    result = await validator_node(state)

    assert result["status"] == AgentStatus.FAILED
    assert any("REFINEMENT_LIMIT_EXCEEDED" in err for err in result["validation_errors"])
    assert result["generated_definition"].status == AgentStatus.FAILED
