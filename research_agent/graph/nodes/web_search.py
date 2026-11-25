"""Web search node.
Executes the planner's web sub‑queries using DuckDuckGo instant answer API.
Stores raw results in `state.raw_web`. Errors are captured in `state.limitations`.
"""

from typing import List

from ..state import ResearchState
from ...tools.web_search_client import search_web, WebResult
from ...shared.schemas.research import Limitation

async def web_search(state: ResearchState) -> ResearchState:
    plan = state.plan or {}
    queries: List[str] = plan.get("web", [])
    all_results: List[WebResult] = []
    for q in queries:
        try:
            results = await search_web(q, limit=5)
            all_results.extend(results)
        except Exception as exc:
            state.limitations.append(
                Limitation(source="web", message=f"Web search failed for '{q}': {exc}")
            )
    state.raw_web = all_results
    return state
