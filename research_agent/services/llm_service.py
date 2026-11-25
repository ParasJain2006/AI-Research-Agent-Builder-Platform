'''LLM service wrapper.
Provides a simple async interface to any OpenAI‑compatible chat completion API.
The wrapper respects the environment variables defined in `.env.example`.
''' 

import os
import json
from typing import Any, Dict, Optional, List

import httpx
from pydantic import BaseModel

# Load configuration from environment (already loaded via python‑dotenv in runtime)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.getenv("LLM_API_KEY")

BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    # add more providers as needed
}

BASE_URL = BASE_URLS.get(LLM_PROVIDER.lower(), "https://api.openai.com/v1")

HEADERS = {
    "Authorization": f"Bearer {LLM_API_KEY}" if LLM_API_KEY else "",
    "Content-Type": "application/json",
}

class LLMResult(BaseModel):
    """Simple container for the LLM raw response.
    `content` holds the final assistant message.
    `response` holds the full JSON payload (useful for debugging).
    """
    content: str
    response: Dict[str, Any]

async def generate(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> LLMResult:
    """Call the LLM and return a structured result.

    Parameters
    ----------
    user_prompt: str
        The user's message.
    system_prompt: Optional[str]
        Optional system instruction.
    response_format: Optional[Dict]
        OpenAI style `{"type": "json_object"}` to request structured JSON.
    temperature: float
        Sampling temperature (default 0 for deterministic output).
    max_tokens: int
        Token limit for the assistant reply.
    """
    payload: Dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": [],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system_prompt:
        payload["messages"].append({"role": "system", "content": system_prompt})
    payload["messages"].append({"role": "user", "content": user_prompt})
    if response_format:
        payload["response_format"] = response_format

    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
        resp = await client.post(f"{BASE_URL}/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        # Extract the assistant message
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception:
            content = ""
        return LLMResult(content=content, response=data)
