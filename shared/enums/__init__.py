"""Enumerations shared across the platform.
Only the enums required by the Research Agent are defined here.
They match exactly the definitions in `TEAM_INTEGRATION_SPEC.md`.
"""

from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchStatus(str, Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    SEARCHING = "searching"
    FILTERING = "filtering"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
