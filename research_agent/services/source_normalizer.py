"""Service to normalize raw provider data into the canonical EvidenceItem schema.
All adapters return their own lightweight models; this module converts them.
"""

from typing import List
from uuid import uuid4

from ..tools.github_client import GitHubRepo
from ..tools.paper_client import PaperInfo
from ..tools.web_search_client import WebResult
from ..tools.wikipedia_client import WikipediaResult

from ..shared.schemas.research import EvidenceItem


def _gen_id() -> str:
    return f"e{uuid4().hex[:8]}"


def normalize_github(repos: List[GitHubRepo]) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []
    for r in repos:
        evidence.append(
            EvidenceItem(
                id=_gen_id(),
                source="github",
                title=r.name,
                url=r.html_url,
                snippet=r.description,
                metadata={
                    "stars": r.stargazers_count,
                    "forks": r.forks_count,
                    "language": r.language,
                    "topics": r.topics,
                    "updated_at": r.updated_at,
                },
            )
        )
    return evidence


def normalize_papers(papers: List[PaperInfo]) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []
    for p in papers:
        evidence.append(
            EvidenceItem(
                id=_gen_id(),
                source="paper",
                title=p.title,
                url=p.url or f"https://www.semanticscholar.org/paper/{p.paper_id}",
                snippet=p.abstract,
                metadata={"year": p.year, "citations": p.citation_count, "authors": p.authors},
            )
        )
    return evidence


def normalize_web(results: List[WebResult]) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []
    for r in results:
        evidence.append(
            EvidenceItem(
                id=_gen_id(),
                source="web",
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                metadata={},
            )
        )
    return evidence


def normalize_wikipedia(results: List[WikipediaResult]) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []
    for r in results:
        evidence.append(
            EvidenceItem(
                id=_gen_id(),
                source="wikipedia",
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                metadata={},
            )
        )
    return evidence
