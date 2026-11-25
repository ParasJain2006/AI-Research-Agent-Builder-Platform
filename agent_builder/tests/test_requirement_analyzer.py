"""
agent_builder.tests.test_requirement_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the requirement_analyzer node.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from shared.enums.status import AgentStatus, SourceType
from shared.schemas.agent import AgentBuildRequest
from shared.schemas.common import SourceReference
from shared.schemas.research import ResearchToAgentRequest
from agent_builder.graph.nodes.requirement_analyzer import requirement_analyzer_node
from agent_builder.graph.state import AgentBuilderState


def create_state(
    research_context: ResearchToAgentRequest | None = None,
) -> AgentBuilderState:
    return {
        "user_id": "usr_test",
        "request_id": "req_test",
        "session_id": "ses_test",
        "build_request": AgentBuildRequest(
            session_id="ses_test",
            agent_name="CodeReviewAgent",
            description="Analyzes GitHub PRs and code quality",
            objective="Inspect commits and review code standards",
            required_tools=["github_search"],
            constraints=["Python 3.10+ only"],
            research_context=research_context,
        ),
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


@pytest.mark.asyncio
async def test_direct_build_no_research_context():
    state = create_state(research_context=None)
    mock_payload = {
        "objective": "Inspect commits and review code standards for quality",
        "capabilities": ["Inspect GitHub PRs", "Check style conventions"],
        "constraints": ["Python 3.10+ only"],
        "suggested_tools": ["github_search"],
    }
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=json.dumps(mock_payload))
    )

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm):
        result = await requirement_analyzer_node(state)

    assert result["status"] == AgentStatus.ANALYZING
    reqs = result["analyzed_requirements"]
    assert "objective" in reqs
    assert "capabilities" in reqs
    assert "constraints" in reqs
    assert "suggested_tools" in reqs
    assert reqs["suggested_tools"] == ["github_search"]


@pytest.mark.asyncio
async def test_research_context_enriches_requirements():
    research_ctx = ResearchToAgentRequest(
        session_id="ses_test",
        research_id="res_abc123",
        original_query="What are best practices for automated PR review?",
        research_summary="AST-based static analysis combined with LLM explanations yields best results.",
        key_findings=[
            "Direct AST checks catch 80% of syntax errors",
            "LLM works best for architectural suggestions",
        ],
        recommended_approach="Use GitHub API to fetch diffs then run two-stage analysis",
        sources=[
            SourceReference(
                source_id="src_1",
                source_type=SourceType.WEB,
                title="Effective Code Reviews",
                url="https://example.com/reviews",
                retrieved_at="2026-11-15T00:00:00Z",
            )
        ],
    )
    state = create_state(research_context=research_ctx)

    mock_llm = MagicMock()
    captured_messages = []

    async def mock_ainvoke(messages):
        captured_messages.extend(messages)
        return MagicMock(
            content=json.dumps({
                "objective": "Two-stage PR review agent using GitHub diffs",
                "capabilities": ["Fetch diffs via GitHub", "Analyze code quality"],
                "constraints": ["Python 3.10+ only"],
                "suggested_tools": ["github_search", "documentation_search"],
            })
        )

    mock_llm.ainvoke = mock_ainvoke

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm):
        result = await requirement_analyzer_node(state)

    assert result["status"] == AgentStatus.ANALYZING
    # Verify the prompt passed to LLM included the research context
    user_prompt_text = captured_messages[1].content
    assert "AST-based static analysis" in user_prompt_text
    assert "Direct AST checks catch 80%" in user_prompt_text
    assert "Use GitHub API to fetch diffs" in user_prompt_text


@pytest.mark.asyncio
async def test_markdown_fences_handled():
    state = create_state()
    fenced_content = """```json
{
  "objective": "Review code",
  "capabilities": ["code review"],
  "constraints": [],
  "suggested_tools": ["github_search"]
}
```"""
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content=fenced_content))

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm):
        result = await requirement_analyzer_node(state)

    assert result["status"] == AgentStatus.ANALYZING
    assert result["analyzed_requirements"]["objective"] == "Review code"


@pytest.mark.asyncio
async def test_malformed_llm_response_handled():
    state = create_state()
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(
        return_value=MagicMock(content="Sorry, I cannot produce JSON right now.")
    )

    with patch("agent_builder.graph.nodes.requirement_analyzer.get_llm_client", return_value=mock_llm):
        result = await requirement_analyzer_node(state)

    assert result["status"] == AgentStatus.FAILED
    assert any("REQUIREMENT_ANALYSIS_FAILED" in err for err in result["errors"])
