"""Planner node.
Takes the analysis from requirement_analyzer and produces a dict mapping each
source to a list of sub‑queries (max 3 per source).
Uses the LLM with a JSON response format.
"""

import json
from typing import Any, Dict, List

from ..state import ResearchState
from ...services.llm_service import generate, LLMResult
from ...prompts.planner import SYSTEM_PROMPT

async def planner(state: ResearchState) -> ResearchState:
    analysis = state.analysis or {}
    normalized_query = analysis.get("normalized_query", state.request.query)
    keywords = analysis.get("keywords", [])
    source_prefs: List[str] = analysis.get("source_preferences", state.request.source_types)

    # Build a concise prompt for the LLM
    user_prompt = f"Query: {normalized_query}\nKeywords: {', '.join(keywords)}"

    llm_res: LLMResult = await generate(
        user_prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        response_format={"type": "json_object"},
    )
    try:
        plan = json.loads(llm_res.content)
    except Exception:
        # Fallback: simple heuristic – use the normalized query for each source
        plan = {src: [normalized_query] for src in source_prefs}

    # Ensure we only keep allowed sources and limit to 3 entries per source
    filtered_plan: Dict[str, List[str]] = {}
    for src in source_prefs:
        queries = plan.get(src, [])
        if not isinstance(queries, list):
            queries = [str(queries)]
        filtered_plan[src] = queries[:3]
    state.plan = filtered_plan
    return state
