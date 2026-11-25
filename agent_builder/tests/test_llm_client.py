"""
agent_builder.tests.test_llm_client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit tests for the centralized Groq LLM client factory.
"""

from __future__ import annotations

import os
from unittest.mock import patch
import pytest

from langchain_groq import ChatGroq
from agent_builder.services.llm_client import LLMConfigurationError, get_llm_client


def test_missing_api_key_raises_configuration_error():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(LLMConfigurationError) as exc_info:
            get_llm_client()

    assert "GROQ_API_KEY environment variable is missing" in str(exc_info.value)


def test_groq_client_initialized_with_default_model():
    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_dummy_123"}, clear=True):
        client = get_llm_client()

    assert isinstance(client, ChatGroq)
    assert client.model_name == "openai/gpt-oss-120b"
    assert client.temperature == 0.1


def test_groq_client_respects_custom_model_env():
    with patch.dict(
        os.environ,
        {"GROQ_API_KEY": "gsk_test_key_dummy_123", "LLM_MODEL": "custom-model-name"},
        clear=True,
    ):
        client = get_llm_client()

    assert isinstance(client, ChatGroq)
    assert client.model_name == "custom-model-name"


def test_groq_client_respects_explicit_parameters():
    client = get_llm_client(
        provider="groq",
        model="explicit-model-120b",
        api_key="gsk_explicit_key_456",
    )

    assert isinstance(client, ChatGroq)
    assert client.model_name == "explicit-model-120b"


def test_unsupported_provider_raises_configuration_error():
    with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_test_key_dummy_123"}, clear=True):
        with pytest.raises(LLMConfigurationError) as exc_info:
            get_llm_client(provider="unsupported_provider")

    assert "Unsupported LLM provider 'unsupported_provider'" in str(exc_info.value)


