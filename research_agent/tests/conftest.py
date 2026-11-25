"""Common fixtures for Research Agent tests."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from shared.schemas.research import ResearchRequest

@pytest.fixture
def sample_request():
    return ResearchRequest(
        session_id="test-session",
        query="Best approaches for building a LangGraph code review agent",
        source_types=["github", "paper", "web"],
        max_sources=5,
        user_constraints=[],
    )

@pytest.fixture
def mock_llm():
    with patch("research_agent.services.llm_service.generate", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_github():
    with patch("research_agent.tools.github_client.GitHubClient.search_repos", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_paper():
    with patch("research_agent.tools.paper_client.PaperClient.search_papers", new_callable=AsyncMock) as mock:
        yield mock

@pytest.fixture
def mock_web():
    with patch("research_agent.tools.web_search_client.search_web", new_callable=AsyncMock) as mock:
        yield mock
