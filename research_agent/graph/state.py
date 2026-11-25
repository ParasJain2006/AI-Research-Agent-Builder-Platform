"""State models for the Research Agent LangGraph workflow.
These models are kept lightweight; they are persisted only in‑memory during a run.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..services.llm_service import LLMResult
from ..tools.github_client import GitHubRepo
from ..tools.paper_client import PaperInfo
from ..tools.web_search_client import WebResult
from ..tools.wikipedia_client import WikipediaResult
from ..shared.schemas.research import ResearchRequest, EvidenceItem, Limitation


class ResearchState(BaseModel):
    """LangGraph state container.
    All node functions read/write to this mutable object.
    """

    request: ResearchRequest = Field(...)
    analysis: Optional[Dict[str, Any]] = None  # output of requirement_analyzer
    plan: Optional[Dict[str, List[str]]] = None  # source -> list of sub‑queries
    raw_github: List[GitHubRepo] = Field(default_factory=list)
    raw_papers: List[PaperInfo] = Field(default_factory=list)
    raw_web: List[WebResult] = Field(default_factory=list)
    raw_wikipedia: List[WikipediaResult] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    limitations: List[Limitation] = Field(default_factory=list)
    synthesis: Optional[Dict[str, Any]] = None  # final report pieces
    class Config:
        arbitrary_types_allowed = True
