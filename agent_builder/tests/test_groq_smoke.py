"""
agent_builder.tests.test_groq_smoke
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Live API smoke test for ChatGroq with model 'openai/gpt-oss-120b'.

Only executes when GROQ_API_KEY is present in the environment.
Otherwise skipped cleanly to allow hermetic CI and local test execution.
"""

from __future__ import annotations

import os
import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from shared.schemas.agent import AgentNodeDefinition
from agent_builder.services.llm_client import get_llm_client
from agent_builder.utils.json_parser import extract_json

HAS_GROQ_API_KEY = bool(os.environ.get("GROQ_API_KEY", "").strip())


@pytest.mark.skipif(not HAS_GROQ_API_KEY, reason="GROQ_API_KEY not configured in environment.")
@pytest.mark.asyncio
async def test_live_groq_structured_output():
    """Verify that ChatGroq with openai/gpt-oss-120b produces parseable structured JSON
    that validates against Agent Builder Pydantic models.
    """
    llm = get_llm_client()

    system_prompt = (
        "You are an AI assistant. Always respond with strictly valid JSON without "
        "markdown code fences or explanation."
    )
    user_prompt = (
        "Output a single JSON object representing a workflow node with the following keys:\n"
        "- node_id: 'search_papers'\n"
        "- node_type: 'search'\n"
        "- description: 'Searches academic repositories'\n"
        "- allowed_tools: ['paper_search']\n"
    )

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    parsed = extract_json(response.content)
    assert isinstance(parsed, dict)

    # Validate against Pydantic model
    node = AgentNodeDefinition.model_validate(parsed)
    assert node.node_id == "search_papers"
    assert node.node_type == "search"
    assert "paper_search" in node.allowed_tools
