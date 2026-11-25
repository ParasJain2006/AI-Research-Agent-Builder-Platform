"""
shared.schemas.common
~~~~~~~~~~~~~~~~~~~~~~
Shared Pydantic models used across research and agent-builder domains.

Models here represent cross-cutting concepts: source references, evidence
items, service request context, and generic API responses.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from shared.enums.status import SourceType


class SourceReference(BaseModel):
    """A reference to a single research source."""

    source_id: str
    source_type: SourceType
    title: str
    url: str
    authors: List[str] = []
    published_at: Optional[str] = None
    retrieved_at: str
    snippet: Optional[str] = None


class EvidenceItem(BaseModel):
    """A single piece of evidence extracted from a source."""

    evidence_id: str
    source_id: str
    claim: str
    supporting_text: Optional[str] = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)


class ServiceContext(BaseModel):
    """Contextual metadata propagated through inter-service requests."""

    user_id: str
    request_id: str
    correlation_id: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class ApiResponse(BaseModel):
    """Standard envelope for all API responses."""

    success: bool
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    error: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: str
