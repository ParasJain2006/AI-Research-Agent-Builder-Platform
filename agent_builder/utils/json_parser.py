"""
agent_builder.utils.json_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Robust JSON extraction helper for LLM responses.
"""

from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> Any:
    """Extract and parse JSON from an LLM response string.

    Handles:
    - Pure JSON strings.
    - Markdown fenced code blocks: ```json ... ``` or ``` ... ```.
    - Embedded JSON object or array within surrounding narrative text.

    Raises
    ------
    ValueError:
        If valid JSON cannot be found or parsed.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Cannot extract JSON from empty or non-string input.")

    stripped = text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2. Check for markdown code fences
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, stripped, re.IGNORECASE)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # 3. Search for outermost { ... }
    first_brace = stripped.find("{")
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = stripped[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 4. Search for outermost [ ... ]
    first_bracket = stripped.find("[")
    last_bracket = stripped.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = stripped[first_bracket : last_bracket + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON could be extracted from text: {text[:200]}...")
