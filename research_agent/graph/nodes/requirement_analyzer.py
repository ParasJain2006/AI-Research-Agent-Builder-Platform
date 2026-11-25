"""Requirement Analyzer node.
Calls the LLM with the user query and extracts a normalized query,
keywords and source preferences.
"""

import json
from typing import Any

from ..state import ResearchState
from ...services.llm_service import generate, LLMResult
from ...prompts.requirement_analyzer import SYSTEM_PROMPT

async def requirement_analyzer(state: ResearchState) -> ResearchState:
    # Build prompt from request
    user_prompt = state.request.query
    # Call LLM expecting JSON output
    llm_res: LLMResult = await generate(
        user_prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        response_format={"type": "json_object"},
    )
    try:
        parsed = json.loads(llm_res.content)
    except Exception as exc:
        # Fallback to minimal info if parsing fails
        parsed = {
            "normalized_query": state.request.query,
            "keywords": [],
            "source_preferences": state.request.source_types,
        }
    state.analysis = parsed
    return state
