"""
shared.exceptions.base
~~~~~~~~~~~~~~~~~~~~~~~
Application exception hierarchy for the CSE AI platform.

Every exception carries a machine-readable ``code`` and a human-readable
``message`` so that API error responses can be generated uniformly.
"""

from __future__ import annotations


class AppBaseException(Exception):
    """Base class for all CSE AI platform exceptions.

    Parameters
    ----------
    message:
        Human-readable description of the error.
    code:
        Machine-readable error code (e.g. ``"INVALID_REQUEST"``).
    """

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ---------------------------------------------------------------------------
# 4xx – client errors
# ---------------------------------------------------------------------------


class InvalidRequestError(AppBaseException):
    """Raised when the incoming request is malformed or logically invalid."""

    def __init__(self, message: str = "Invalid request.") -> None:
        super().__init__(message=message, code="INVALID_REQUEST")


class ValidationError(AppBaseException):
    """Raised when request payload fails schema or business-rule validation."""

    def __init__(self, message: str = "Validation error.") -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")


class UnauthorizedError(AppBaseException):
    """Raised when the caller is not authenticated."""

    def __init__(self, message: str = "Unauthorized.") -> None:
        super().__init__(message=message, code="UNAUTHORIZED")


class ForbiddenError(AppBaseException):
    """Raised when the authenticated caller lacks permission for the action."""

    def __init__(self, message: str = "Forbidden.") -> None:
        super().__init__(message=message, code="FORBIDDEN")


class NotFoundError(AppBaseException):
    """Raised when a requested resource does not exist.

    Parameters
    ----------
    entity_type:
        Human-readable name of the entity that was not found
        (e.g. ``"ResearchSession"``).
    message:
        Optional override for the default "X not found." message.
    """

    def __init__(self, entity_type: str, message: str | None = None) -> None:
        if message is None:
            message = f"{entity_type} not found."
        super().__init__(message=message, code="NOT_FOUND")
        self.entity_type = entity_type


class ConflictError(AppBaseException):
    """Raised when an action conflicts with the resource's current state."""

    def __init__(self, message: str = "Invalid state transition.") -> None:
        super().__init__(message=message, code="INVALID_STATE_TRANSITION")


class RateLimitedError(AppBaseException):
    """Raised when a client or downstream service has exceeded its rate limit."""

    def __init__(self, message: str = "Rate limit exceeded.") -> None:
        super().__init__(message=message, code="RATE_LIMITED")


# ---------------------------------------------------------------------------
# 5xx – server / downstream errors
# ---------------------------------------------------------------------------


class InternalError(AppBaseException):
    """Raised when an unexpected server-side error occurs."""

    def __init__(self, message: str = "Internal server error.") -> None:
        super().__init__(message=message, code="INTERNAL_ERROR")


class SourceUnavailableError(AppBaseException):
    """Raised when a research source (GitHub, arXiv, etc.) cannot be reached."""

    def __init__(self, message: str = "Source unavailable.") -> None:
        super().__init__(message=message, code="SOURCE_UNAVAILABLE")


class ToolNotAllowedError(AppBaseException):
    """Raised when an agent requests a tool that is not in the approved registry.

    Parameters
    ----------
    tool_name:
        The name of the disallowed tool.
    """

    def __init__(self, tool_name: str) -> None:
        super().__init__(
            message=f"Tool '{tool_name}' is not allowed.",
            code="TOOL_NOT_ALLOWED",
        )
        self.tool_name = tool_name


# ---------------------------------------------------------------------------
# Agent-builder specific errors
# ---------------------------------------------------------------------------


class AgentGenerationFailed(AppBaseException):
    """Raised when the LLM-based agent generation step fails."""

    def __init__(self, message: str = "Agent generation failed.") -> None:
        super().__init__(message=message, code="AGENT_GENERATION_FAILED")


class AgentValidationFailed(AppBaseException):
    """Raised when a generated agent definition fails structural validation."""

    def __init__(self, message: str = "Agent validation failed.") -> None:
        super().__init__(message=message, code="AGENT_VALIDATION_FAILED")
