"""Research Agent LangGraph workflow definition.
The graph follows the contract:
START → requirement_analyzer → planner → parallel searches (GitHub, Paper, Web) →
    evidence_filter → synthesizer → END
Failures in any search node are recorded as limitations and do not abort the workflow.
"""

from langgraph.graph import StateGraph, END
from .state import ResearchState
from .nodes.requirement_analyzer import requirement_analyzer
from .nodes.planner import planner
from .nodes.github_search import github_search
from .nodes.paper_search import paper_search
from .nodes.web_search import web_search
from .nodes.evidence_filter import evidence_filter
from .nodes.synthesizer import synthesizer


def build_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    # Register all nodes
    graph.add_node("requirement_analyzer", requirement_analyzer)
    graph.add_node("planner", planner)
    graph.add_node("github_search", github_search)
    graph.add_node("paper_search", paper_search)
    graph.add_node("web_search", web_search)
    graph.add_node("evidence_filter", evidence_filter)
    graph.add_node("synthesizer", synthesizer)

    # Define sequential edges that enforce a simple fan‑out → join pattern
    graph.add_edge("requirement_analyzer", "planner")
    # After planning, all three searches run in parallel. LangGraph treats multiple outgoing edges
    # as a fan‑out; each target receives the same state.
    graph.add_edge("planner", "github_search")
    graph.add_edge("planner", "paper_search")
    graph.add_edge("planner", "web_search")

    # Join point – after each search completes, we forward to the same join node.
    # Implement the join as a no‑op node that simply returns the state; then continue.
    def _join(state: ResearchState) -> ResearchState:
        return state

    graph.add_node("_join", _join)
    graph.add_edge("github_search", "_join")
    graph.add_edge("paper_search", "_join")
    graph.add_edge("web_search", "_join")

    # After all searches have converged, continue to filtering and synthesis.
    graph.add_edge("_join", "evidence_filter")
    graph.add_edge("evidence_filter", "synthesizer")
    graph.add_edge("synthesizer", END)

    # Entry point
    graph.set_entry_point("requirement_analyzer")
    return graph
