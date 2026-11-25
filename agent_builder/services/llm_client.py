"""
agent_builder.services.llm_client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LLM client factory for the Agent Builder module.

Configured to use Groq as the primary LLM provider with ChatGroq and model
'openai/gpt-oss-120b'. Requires GROQ_API_KEY to be set in the environment.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from langchain_groq import ChatGroq
from shared.exceptions.base import InternalError

logger = logging.getLogger(__name__)


class LLMConfigurationError(InternalError, ValueError):
    """Raised when the LLM client is missing required configuration (e.g. API key)."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message)


def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ChatGroq:
    """Return a configured ChatGroq client based on environment and parameters.

    Parameters
    ----------
    provider:
        Optional provider override (defaults to LLM_PROVIDER or 'groq').
    model:
        Optional model override (defaults to LLM_MODEL or 'openai/gpt-oss-120b').
    api_key:
        Optional API key override (defaults to GROQ_API_KEY env var).

    Returns
    -------
    ChatGroq
        Configured LangChain ChatGroq instance.

    Raises
    ------
    LLMConfigurationError
        If GROQ_API_KEY is missing or empty.
    """
    resolved_provider = (provider or os.environ.get("LLM_PROVIDER", "groq")).strip().lower()
    if resolved_provider != "groq":
        raise LLMConfigurationError(
            f"Unsupported LLM provider '{resolved_provider}'. "
            f"Agent Builder explicitly requires 'groq' as the LLM provider."
        )
    resolved_model = model or os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
    resolved_key = (api_key or os.environ.get("GROQ_API_KEY", "")).strip()

    if not resolved_key:
        raise LLMConfigurationError(
            f"GROQ_API_KEY environment variable is missing or empty. "
            f"Please set GROQ_API_KEY to initialize the '{resolved_provider}' LLM client "
            f"with model '{resolved_model}'."
        )

    logger.debug(
        "Initializing ChatGroq client with model=%s, provider=%s",
        resolved_model,
        resolved_provider,
    )

    return ChatGroq(
        model=resolved_model,
        api_key=resolved_key,
        temperature=0.1,  # low temperature for reliable structured output
    )
