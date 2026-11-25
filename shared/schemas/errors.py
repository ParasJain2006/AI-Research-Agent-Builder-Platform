"""
shared.schemas.errors
~~~~~~~~~~~~~~~~~~~~~~
Pydantic model for a structured API error payload.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Represents a single structured error returned in an API response."""

    code: str
    message: str
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
