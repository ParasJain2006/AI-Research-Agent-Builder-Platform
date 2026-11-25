"""
agent_builder.tests.test_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contract and integration tests for the public Agent Builder service interface.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from shared.enums.status import AgentStatus
from shared.exceptions.base import AgentGenerationFailed
from shared.schemas.agent import (
    AgentBuildRequest,
    AgentDefinition,
    AgentEdgeDefinition,
    AgentNodeDefinition,
    AgentTestRequest,
)
from shared.schemas.common import ServiceContext
from agent_builder.service import build_agent, test_agent as service_test_agent

# Prevent pytest from mistaking the imported service function for a test case
service_test_agent.__test__ = False


def create_context() -> ServiceContext:
    return ServiceContext(
        user_id="usr_prod_test",
        request_id="req_prod_test",
        llm_provider="groq",
        llm_model="openai/gpt-oss-120b",
    )


def create_sample_agent(tools: list[str] = None) -> AgentDefinition:
    if tools is None:
        tools = ["web_search", "paper_search"]
    return AgentDefinition(
        agent_id="agt_service_test",
        agent_name="SampleResearcher",
        description="Assists in academic paper discovery",
        objective="Find relevant papers and summarize key findings",
        system_prompt="You are SampleResearcher. Search academic literature accurately.",
        tools=tools,
        workflow_nodes=[
            AgentNodeDefinition(
                node_id="search",
                node_type="search",
                description="Search papers",
                allowed_tools=["paper_search"],
            ),
            AgentNodeDefinition(
                node_id="synthesize",
                node_type="synthesizer",
                description="Synthesize results",
                allowed_tools=[],
            ),
        ],
        workflow_edges=[
            AgentEdgeDefinition(source_node="search", target_node="synthesize")
        ],
        entry_node="search",
        constraints=["Do not hallucinate citations"],
        status=AgentStatus.READY,
        schema_version="1.0",
        created_at="2026-11-15T00:00:00Z",
        updated_at="2026-11-15T00:00:00Z",
    )


@pytest.mark.asyncio
async def test_build_agent_success_returns_agent_definition():
    request = AgentBuildRequest(
        session_id="ses_123",
        agent_name="SampleResearcher",
        description="Assists in academic paper discovery",
        objective="Find relevant papers and summarize key findings",
    )
    context = create_context()
    sample_def = create_sample_agent()

    mock_graph_return = {
        "status": AgentStatus.READY,
        "generated_definition": sample_def,
        "errors": [],
    }

    with patch("agent_builder.service.agent_builder_graph.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_graph_return
        result = await build_agent(request, context)

    assert isinstance(result, AgentDefinition)
    assert result.status == AgentStatus.READY
    assert result.agent_name == "SampleResearcher"
    assert result.tools == ["web_search", "paper_search"]


@pytest.mark.asyncio
async def test_build_agent_failure_raises_agent_generation_failed():
    request = AgentBuildRequest(
        session_id="ses_123",
        agent_name="BrokenAgent",
        description="Fails generation",
        objective="Demonstrate error handling",
    )
    context = create_context()

    mock_graph_return = {
        "status": AgentStatus.FAILED,
        "generated_definition": None,
        "errors": ["TOOL_NOT_ALLOWED: No approved tools could be selected."],
        "validation_errors": [],
    }

    with patch("agent_builder.service.agent_builder_graph.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_graph_return
        with pytest.raises(AgentGenerationFailed) as exc_info:
            await build_agent(request, context)

    assert "TOOL_NOT_ALLOWED" in str(exc_info.value)


@pytest.mark.asyncio
async def test_test_agent_controlled_execution():
    agent = create_sample_agent()
    test_request = AgentTestRequest(
        input_text="What are recent breakthroughs in transformer models?",
        test_context={"domain": "machine-learning"},
    )
    context = create_context()

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content="Here are recent transformer breakthroughs...")
    )

    with patch("agent_builder.service.get_llm_client", return_value=mock_llm):
        result = await service_test_agent(agent, test_request, context)

    assert result.success is True
    assert result.output == "Here are recent transformer breakthroughs..."
    assert len(result.execution_trace) >= 5
    assert any("validation" in trace.lower() for trace in result.execution_trace)
    assert any("Verified approved tools" in trace for trace in result.execution_trace)


@pytest.mark.asyncio
async def test_test_agent_catches_invalid_structure_before_llm():
    """Verify test_agent performs complete deterministic validation and rejects invalid
    agent structure before any LLM invocation.
    """
    # Create agent with unreachable node (violates graph connectivity)
    nodes = [
        AgentNodeDefinition(
            node_id="entry_node",
            node_type="search",
            description="Entry",
            allowed_tools=["web_search"],
        ),
        AgentNodeDefinition(
            node_id="isolated_node",
            node_type="task",
            description="Isolated",
            allowed_tools=[],
        ),
    ]
    invalid_agent = create_sample_agent()
    invalid_agent.workflow_nodes = nodes
    invalid_agent.workflow_edges = []  # No edge to isolated_node
    invalid_agent.entry_node = "entry_node"

    test_request = AgentTestRequest(input_text="Test prompt")
    context = create_context()

    # If LLM was invoked, this test would fail because mock is NOT provided
    result = await service_test_agent(invalid_agent, test_request, context)

    assert result.success is False
    assert any("GRAPH_CONNECTIVITY_ERROR" in err for err in result.errors)
    assert result.output is None



@pytest.mark.asyncio
async def test_test_agent_catches_unapproved_tool():
    agent = create_sample_agent(tools=["web_search", "unauthorized_arbitrary_cmd"])
    test_request = AgentTestRequest(
        input_text="Test prompt",
    )
    context = create_context()

    result = await service_test_agent(agent, test_request, context)

    assert result.success is False
    assert any("TOOL_NOT_ALLOWED" in err for err in result.errors)
    assert any("unauthorized_arbitrary_cmd" in err for err in result.errors)
    assert result.output is None


@pytest.mark.asyncio
async def test_end_to_end_research_agent_use_case():
    """Validates Use Case 1: Research Agent (web_search, paper_search)."""
    request = AgentBuildRequest(
        session_id="ses_usecase_1",
        agent_name="LiteratureResearcher",
        description="Search web and academic papers for literature review",
        objective="Find academic papers and summarize recent discoveries",
        required_tools=["paper_search", "web_search"],
    )
    context = create_context()

    # Setup sequential LLM mocks for the 4 LLM nodes in the pipeline:
    # 1. requirement_analyzer
    # 2. tool_selector
    # 3. architecture_designer
    # 4. agent_generator
    responses = [
        # requirement_analyzer
        MagicMock(content=json.dumps({
            "objective": "Find academic papers and summarize recent discoveries",
            "capabilities": ["Search scientific papers", "Search web documentation"],
            "constraints": ["Cite sources"],
            "suggested_tools": ["paper_search", "web_search"],
        })),
        # tool_selector
        MagicMock(content=json.dumps(["paper_search", "web_search"])),
        # architecture_designer
        MagicMock(content=json.dumps({
            "entry_node": "search_literature",
            "workflow_nodes": [
                {
                    "node_id": "search_literature",
                    "node_type": "search",
                    "description": "Searches paper repositories and web",
                    "allowed_tools": ["paper_search", "web_search"],
                },
                {
                    "node_id": "synthesize_findings",
                    "node_type": "synthesize",
                    "description": "Extracts and synthesizes evidence",
                    "allowed_tools": [],
                },
            ],
            "workflow_edges": [
                {
                    "source_node": "search_literature",
                    "target_node": "synthesize_findings",
                    "condition": None,
                }
            ],
        })),
        # agent_generator
        MagicMock(content=json.dumps({
            "system_prompt": "You are LiteratureResearcher. Search papers and web sources to produce rigorous reviews.",
        })),
    ]

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=responses)

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.architecture_designer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.agent_generator.get_llm_client", return_value=mock_llm):
        definition = await build_agent(request, context)

    assert isinstance(definition, AgentDefinition)
    assert definition.status == AgentStatus.READY
    assert definition.agent_name == "LiteratureResearcher"
    assert set(definition.tools) == {"paper_search", "web_search"}
    assert definition.entry_node == "search_literature"


@pytest.mark.asyncio
async def test_end_to_end_github_developer_agent_use_case():
    """Validates Use Case 2: GitHub / Developer Agent (github_search, documentation_search, web_search)."""
    request = AgentBuildRequest(
        session_id="ses_usecase_2",
        agent_name="GitHubDeveloperAgent",
        description="Search GitHub repos and technical docs to compare libraries",
        objective="Compare GitHub repositories and official documentation",
        required_tools=["github_search", "documentation_search", "web_search"],
    )
    context = create_context()

    responses = [
        # requirement_analyzer
        MagicMock(content=json.dumps({
            "objective": "Compare GitHub repositories and official documentation",
            "capabilities": ["Search repositories", "Query technical documentation"],
            "constraints": ["Open source only"],
            "suggested_tools": ["github_search", "documentation_search", "web_search"],
        })),
        # tool_selector
        MagicMock(content=json.dumps(["github_search", "documentation_search", "web_search"])),
        # architecture_designer
        MagicMock(content=json.dumps({
            "entry_node": "fetch_repos",
            "workflow_nodes": [
                {
                    "node_id": "fetch_repos",
                    "node_type": "search",
                    "description": "Searches GitHub and docs",
                    "allowed_tools": ["github_search", "documentation_search"],
                },
                {
                    "node_id": "compare_features",
                    "node_type": "compare",
                    "description": "Compares architectures and APIs",
                    "allowed_tools": ["web_search"],
                },
            ],
            "workflow_edges": [
                {
                    "source_node": "fetch_repos",
                    "target_node": "compare_features",
                    "condition": None,
                }
            ],
        })),
        # agent_generator
        MagicMock(content=json.dumps({
            "system_prompt": "You are GitHubDeveloperAgent. Search GitHub repositories and documentation to compare technologies.",
        })),
    ]

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=responses)

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.architecture_designer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.agent_generator.get_llm_client", return_value=mock_llm):
        definition = await build_agent(request, context)

    assert isinstance(definition, AgentDefinition)
    assert definition.status == AgentStatus.READY
    assert definition.agent_name == "GitHubDeveloperAgent"
    assert set(definition.tools) == {"github_search", "documentation_search", "web_search"}


@pytest.mark.asyncio
async def test_end_to_end_document_analysis_agent_use_case():
    """Validates Use Case 3: Document Analysis Agent (document_reader)."""
    request = AgentBuildRequest(
        session_id="ses_usecase_3",
        agent_name="DocumentAnalysisAgent",
        description="Read uploaded documents and answer questions",
        objective="Extract data from uploaded PDF documents and answer user questions",
        required_tools=["document_reader"],
    )
    context = create_context()

    responses = [
        # requirement_analyzer
        MagicMock(content=json.dumps({
            "objective": "Extract data from uploaded PDF documents and answer user questions",
            "capabilities": ["Read uploaded files", "Extract tables and text"],
            "constraints": ["Cite document page numbers"],
            "suggested_tools": ["document_reader"],
        })),
        # tool_selector
        MagicMock(content=json.dumps(["document_reader"])),
        # architecture_designer
        MagicMock(content=json.dumps({
            "entry_node": "parse_document",
            "workflow_nodes": [
                {
                    "node_id": "parse_document",
                    "node_type": "reader",
                    "description": "Reads and extracts document contents",
                    "allowed_tools": ["document_reader"],
                },
                {
                    "node_id": "answer_question",
                    "node_type": "qna",
                    "description": "Answers user queries based on extracted content",
                    "allowed_tools": [],
                },
            ],
            "workflow_edges": [
                {
                    "source_node": "parse_document",
                    "target_node": "answer_question",
                    "condition": None,
                }
            ],
        })),
        # agent_generator
        MagicMock(content=json.dumps({
            "system_prompt": "You are DocumentAnalysisAgent. Read uploaded documents with document_reader and answer questions accurately.",
        })),
    ]

    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(side_effect=responses)

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.tool_selector.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.architecture_designer.get_llm_client", return_value=mock_llm), \
         patch("agent_builder.graph.nodes.agent_generator.get_llm_client", return_value=mock_llm):
        definition = await build_agent(request, context)

    assert isinstance(definition, AgentDefinition)
    assert definition.status == AgentStatus.READY
    assert definition.agent_name == "DocumentAnalysisAgent"
    assert definition.tools == ["document_reader"]
    assert definition.entry_node == "parse_document"
