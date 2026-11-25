"""
shared.schemas.agent
~~~~~~~~~~~~~~~~~~~~~
Pydantic models for the Agent Builder domain.

Covers the full lifecycle: build requests, node/edge definitions, complete
agent definitions, test requests/results, and refinement requests.

Depends on:
- shared.enums.status (AgentStatus)
- shared.schemas.research (ResearchToAgentRequest)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from shared.enums.status import AgentStatus
from shared.schemas.research import ResearchToAgentRequest


class AgentNodeDefinition(BaseModel):
    """Definition of a single node in an agent's workflow graph."""

    node_id: str
    node_type: str
    description: str
    allowed_tools: List[str] = []


class AgentEdgeDefinition(BaseModel):
    """A directed edge connecting two nodes in an agent workflow graph."""

    source_node: str
    target_node: str
    condition: Optional[str] = None


class AgentDefinition(BaseModel):
    """Complete, validated definition of a generated AI agent."""

    agent_id: str
    agent_name: str
    description: str
    objective: str
    system_prompt: str
    tools: List[str]
    workflow_nodes: List[AgentNodeDefinition]
    workflow_edges: List[AgentEdgeDefinition]
    entry_node: str
    constraints: List[str] = []
    status: AgentStatus
    schema_version: str = "1.0"
    created_at: str
    updated_at: str


class AgentBuildRequest(BaseModel):
    """Request payload to trigger agent generation via the builder pipeline."""

    session_id: str
    agent_name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=2000)
    objective: str = Field(min_length=3, max_length=2000)
    required_tools: List[str] = []
    constraints: List[str] = []
    research_context: Optional[ResearchToAgentRequest] = None


class AgentTestRequest(BaseModel):
    """Request to run a lightweight test against a generated agent definition."""

    input_text: str = Field(min_length=1, max_length=8000)
    test_context: Dict[str, Any] = {}


class AgentTestResult(BaseModel):
    """Result of a test run against a generated agent."""

    test_id: str
    agent_id: str
    success: bool
    output: Optional[str] = None
    errors: List[str] = []
    execution_trace: List[str] = []
    started_at: str
    completed_at: str


class AgentRefineRequest(BaseModel):
    """Request to refine an existing agent definition."""

    instruction: str = Field(min_length=3, max_length=4000)
    expected_behavior: Optional[str] = None
