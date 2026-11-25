"""Synthesizer node.
Consumes `state.evidence` and calls the LLM to produce a structured research report.
The LLM receives a JSON payload with the evidence items (id, source, title, snippet).
It must return a JSON object with keys: summary, key_findings, recommendations.
The node stores the result in `state.synthesis`.
"""

import json
from typing import List, Dict, Any

from ..state import ResearchState
from ...services.llm_service import generate, LLMResult
from ...prompts.synthesizer import SYSTEM_PROMPT

async def synthesizer(state: ResearchState) -> ResearchState:
    # Prepare evidence payload for the LLM
    evidence_payload = [
        {
            "id": ev.id,
            "source": ev.source,
            "title": ev.title,
            "snippet": ev.snippet,
        }
        for ev in state.evidence
    ]
    user_prompt = json.dumps({"evidence": evidence_payload}, ensure_ascii=False, indent=2)
    llm_res: LLMResult = await generate(
        user_prompt=user_prompt,
        system_prompt=SYSTEM_PROMPT,
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    try:
        report = json.loads(llm_res.content)
    except Exception:
        report = {"summary": "", "key_findings": [], "recommendations": []}
    # Store synthesis dict
    state.synthesis = report
    return state
