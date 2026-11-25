"""Synthesizer prompt.
The LLM receives a JSON array of evidence items (id, source, title, snippet) and must produce a structured research report JSON.
Required keys: summary, key_findings (list), recommendations (list).
Do not fabricate citations – only reference evidence ids present in the input.
Return ONLY the JSON object.
"""
