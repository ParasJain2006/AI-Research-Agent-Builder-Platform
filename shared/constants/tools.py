"""
shared.constants.tools
~~~~~~~~~~~~~~~~~~~~~~~
V1 approved tool registry for the CSE AI platform.

``ALLOWED_TOOL_NAMES`` is the single source of truth for which tool
identifiers agent definitions may reference.  Any tool name not present in
this frozenset must be rejected with a ``ToolNotAllowedError``.
"""

ALLOWED_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "github_search",
        "paper_search",
        "web_search",
        "documentation_search",
        "document_reader",
    }
)
