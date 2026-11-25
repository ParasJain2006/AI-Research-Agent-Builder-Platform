"""Evidence filter node.
* Normalizes raw provider results using `source_normalizer`.
* Deduplicates by URL.
* Removes obviously irrelevant items (e.g., very low star count for GitHub, zero citations for papers).
* Ranks the remaining evidence via `ranking_service.rank_evidence`.
* Stores final evidence list in `state.evidence`.
* Records any filtering limitations.
"""

from typing import List, Set

from ..state import ResearchState
from ...services.source_normalizer import (
    normalize_github,
    normalize_papers,
    normalize_web,
    normalize_wikipedia,
)
from ...services.ranking_service import rank_evidence
from ...shared.schemas.research import Limitation, EvidenceItem

async def evidence_filter(state: ResearchState) -> ResearchState:
    # Normalization
    evidence: List[EvidenceItem] = []
    evidence.extend(normalize_github(state.raw_github))
    evidence.extend(normalize_papers(state.raw_papers))
    evidence.extend(normalize_web(state.raw_web))
    # Wikipedia results are stored in raw_web as well? Not currently. For completeness, handle if present.
    if hasattr(state, "raw_wikipedia"):
        evidence.extend(normalize_wikipedia(state.raw_wikipedia))

    # Deduplicate by URL
    uniq: List[EvidenceItem] = []
    seen: Set[str] = set()
    for ev in evidence:
        if ev.url in seen:
            continue
        seen.add(ev.url)
        uniq.append(ev)
    evidence = uniq

    # Simple relevance filter – drop GitHub repos with <5 stars, papers with <2 citations
    filtered: List[EvidenceItem] = []
    for ev in evidence:
        keep = True
        if ev.source == "github":
            stars = ev.metadata.get("stars", 0)
            if stars < 5:
                keep = False
        elif ev.source == "paper":
            cites = ev.metadata.get("citations", 0)
            if cites < 2:
                keep = False
        if not keep:
            state.limitations.append(
                Limitation(source=ev.source, message=f"Filtered low‑relevance evidence id={ev.id}")
            continue
        filtered.append(ev)

    # Ranking
    ranked = rank_evidence(filtered)
    # Trim to max_sources from request
    max_items = state.request.max_sources
    state.evidence = ranked[:max_items]
    return state
