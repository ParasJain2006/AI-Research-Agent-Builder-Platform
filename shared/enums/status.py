"""
shared.enums.status
~~~~~~~~~~~~~~~~~~~~
Status / state enumerations shared across the CSE AI platform.

Using ``(str, Enum)`` so enum members serialize naturally to their string
values in JSON responses and Pydantic models.
"""

from enum import Enum


class JobStatus(str, Enum):
    """Generic background-job lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchStatus(str, Enum):
    """Lifecycle states for a research session."""

    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    SEARCHING = "searching"
    FILTERING = "filtering"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, Enum):
    """Lifecycle states for an agent-builder session."""

    DRAFT = "draft"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    GENERATING = "generating"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"


class SourceType(str, Enum):
    """Supported research source categories."""

    GITHUB = "github"
    PAPER = "paper"
    WEB = "web"
    DOCUMENTATION = "documentation"
