"""Requirement Analyzer prompt.
The LLM must output a JSON object with the following keys:
- normalized_query: a concise, canonical phrasing of the user's request
- keywords: list of important terms (tech, frameworks, concepts)
- source_preferences: ordered list of sources that make sense for this query.
Only include sources from {"github","paper","web","wikipedia"}.
If the user explicitly mentions a source, honor that preference.
Return ONLY the JSON object (no extra text)."""
