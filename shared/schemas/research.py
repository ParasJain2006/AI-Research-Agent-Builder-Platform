"""
shared.schemas.research
~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic models for research-session request/response payloads.

These models form the contract between the API gateway, the research agent,
and the agent-builder service.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from shared.enums.status import ResearchStatus, SourceType
from shared.schemas.common import EvidenceItem, SourceReference


class ResearchRequest(BaseModel):
    """Parameters for initiating a new research session."""

    session_id: str
    query: str = Field(min_length=3, max_length=4000)
    source_types: List[SourceType] = [
        SourceType.GITHUB,
        SourceType.PAPER,
        SourceType.WEB,
        SourceType.DOCUMENTATION,
    ]
    max_sources: int = Field(default=20, ge=1, le=50)
    user_constraints: List[str] = []


class ResearchResult(BaseModel):
    """The completed output of a research session."""

    research_id: str
    session_id: str
    original_query: str
    normalized_query: str
    summary: str
    key_findings: List[str]
    recommended_approach: Optional[str] = None
    sources: List[SourceReference]
    evidence: List[EvidenceItem] = []
    limitations: List[str] = []
    status: ResearchStatus
    created_at: str
    completed_at: Optional[str] = None


class ResearchToAgentRequest(BaseModel):
    """Payload sent from the research service to the agent-builder service.

    Carries a distilled view of research results so the agent-builder can
    generate a contextually informed agent definition.
    """

    session_id: str
    research_id: str
    original_query: str
    research_summary: str
    key_findings: List[str]
    recommended_approach: Optional[str] = None
    sources: List[SourceReference]
    agent_instruction: Optional[str] = None
