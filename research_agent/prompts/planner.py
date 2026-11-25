"""Planner prompt.
Given the normalized query, extracted keywords and the list of source preferences,
produce a JSON object mapping each source to **up to three** concise sub‑queries.
Only include sources that appear in the `source_preferences` list.
Example output:
{
  "github": ["langgraph code review agent"],
  "paper": ["LLM based code review"],
  "web": ["LangGraph agent documentation"]
}
Return ONLY the JSON object. Do not add extra commentary."""
