"""Test requirement analyzer node with mocked LLM."""
import json
import pytest
from unittest.mock import AsyncMock

from research_agent.graph.nodes.requirement_analyzer import requirement_analyzer
from research_agent.graph.state import ResearchState
from shared.schemas.research import ResearchRequest

@pytest.mark.asyncio
async def test_requirement_analyzer_success(sample_request, mock_llm):
    # Mock LLM to return a JSON string
    mock_llm.return_value = AsyncMock()
    mock_llm.return_value.content = json.dumps({
        "normalized_query": "compare langgraph crewai",
        "keywords": ["langgraph", "crewai", "multi-agent"],
        "source_preferences": ["github", "paper", "web"]
    })
    state = ResearchState(request=sample_request)
    state = await requirement_analyzer(state)
    assert state.analysis["normalized_query"] == "compare langgraph crewai"
    assert "github" in state.analysis["source_preferences"]

@pytest.mark.asyncio
async def test_requirement_analyzer_fallback(sample_request, mock_llm):
    # LLM returns malformed JSON → fallback to defaults
    mock_llm.return_value = AsyncMock()
    mock_llm.return_value.content = "not a json"
    state = ResearchState(request=sample_request)
    state = await requirement_analyzer(state)
    assert state.analysis["normalized_query"] == sample_request.query
    assert set(state.analysis["source_preferences"]).issubset(set(sample_request.source_types))
