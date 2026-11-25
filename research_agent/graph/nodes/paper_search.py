"""Paper search node.
Runs the planner's paper sub‑queries against Semantic Scholar.
Stores raw results in `state.raw_papers`. Errors are captured in `state.limitations`.
"""

from typing import List

from ..state import ResearchState
from ...tools.paper_client import PaperClient, PaperInfo
from ...shared.schemas.research import Limitation

async def paper_search(state: ResearchState) -> ResearchState:
    plan = state.plan or {}
    queries: List[str] = plan.get("paper", [])
    client = PaperClient()
    all_results: List[PaperInfo] = []
    for q in queries:
        try:
            papers = await client.search_papers(q, limit=5)
            all_results.extend(papers)
        except Exception as exc:
            state.limitations.append(
                Limitation(source="paper", message=f"Paper search failed for '{q}': {exc}")
            )
    state.raw_papers = all_results
    return state
