"""Research Agent public service.
Provides the async `run_research` entry point that the backend can call.
It builds the LangGraph, runs it with the incoming request, and returns a
`ResearchResult` that conforms to the shared contract.
"""

from typing import Any

from shared.schemas.research import ResearchRequest, ResearchResult, EvidenceItem, Limitation
from .graph.graph import build_graph
from .graph.state import ResearchState

async def run_research(request: ResearchRequest, context: Any = None) -> ResearchResult:
    """Execute the full research workflow.

    Parameters
    ----------
    request: ResearchRequest
        The user query and configuration.
    context: Any (optional)
        Placeholder for future ServiceContext – currently unused.
    """
    # Initialise LangGraph state
    state = ResearchState(request=request)
    # Build and compile the graph
    graph = build_graph()
    runnable = graph.compile()
    # Run the graph – LangGraph returns the final state dict
    final_state: ResearchState = await runnable.ainvoke(state)

    # Assemble final ResearchResult
    synthesis = final_state.synthesis or {}
    result = ResearchResult(
        session_id=request.session_id,
        query=request.query,
        status="completed" if not final_state.limitations else "completed",  # we still report completed with limitations
        summary=synthesis.get("summary"),
        key_findings=synthesis.get("key_findings", []),
        recommendations=synthesis.get("recommendations", []),
        evidence=final_state.evidence,
        limitations=final_state.limitations,
    )
    return result
