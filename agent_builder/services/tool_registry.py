"""
agent_builder.services.tool_registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Approved tool registry and metadata for V1.

The registry is the single source of truth for tool definitions and capability
inspection in the Agent Builder module. No tool outside of ALLOWED_TOOL_NAMES
may be registered or executed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from shared.constants.tools import ALLOWED_TOOL_NAMES


class ToolDefinition(BaseModel):
    """Metadata describing a registered tool capability."""

    tool_name: str
    description: str
    input_schema: Dict[str, Any]
    risk_level: str
    requires_auth: bool
    enabled: bool = True


TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "github_search": ToolDefinition(
        tool_name="github_search",
        description="Search GitHub repositories, issues, PRs, and code.",
        input_schema={"query": "string", "max_results": "integer"},
        risk_level="low",
        requires_auth=False,
        enabled=True,
    ),
    "paper_search": ToolDefinition(
        tool_name="paper_search",
        description="Search academic publications, preprints, and abstracts.",
        input_schema={"query": "string", "max_results": "integer"},
        risk_level="low",
        requires_auth=False,
        enabled=True,
    ),
    "web_search": ToolDefinition(
        tool_name="web_search",
        description="Search public web sources for technical and general information.",
        input_schema={"query": "string"},
        risk_level="low",
        requires_auth=False,
        enabled=True,
    ),
    "documentation_search": ToolDefinition(
        tool_name="documentation_search",
        description="Search official technical documentation and developer guides.",
        input_schema={"query": "string", "source": "string"},
        risk_level="low",
        requires_auth=False,
        enabled=True,
    ),
    "document_reader": ToolDefinition(
        tool_name="document_reader",
        description="Read, parse, and extract information from uploaded files.",
        input_schema={"document_id": "string", "query": "string"},
        risk_level="low",
        requires_auth=True,
        enabled=True,
    ),
}


def get_tool_definition(tool_name: str) -> Optional[ToolDefinition]:
    """Return the ToolDefinition for a given tool name if registered."""
    return TOOL_REGISTRY.get(tool_name)


def is_tool_allowed(tool_name: str) -> bool:
    """Check whether a tool name is registered, enabled, and in ALLOWED_TOOL_NAMES."""
    if tool_name not in ALLOWED_TOOL_NAMES:
        return False
    tool = TOOL_REGISTRY.get(tool_name)
    return tool is not None and tool.enabled


def list_allowed_tools() -> List[str]:
    """Return a sorted list of all enabled tool names in the registry."""
    return sorted(name for name, t in TOOL_REGISTRY.items() if t.enabled and name in ALLOWED_TOOL_NAMES)
