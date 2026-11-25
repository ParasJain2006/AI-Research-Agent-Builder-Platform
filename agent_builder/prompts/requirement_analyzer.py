"""
agent_builder.prompts.requirement_analyzer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Prompts for extracting structured requirements from build requests.
"""

SYSTEM_PROMPT = """You are an expert AI system analyst and agent requirement engineer.
Your task is to analyze user requests for building an AI agent and distill clear, structured specifications.
You must extract the core objective, required functional capabilities, operational constraints, and recommended tools.

Only recommend tools from the approved registry:
- github_search: Search GitHub repositories, code, issues, and pull requests.
- paper_search: Search academic papers and scientific literature.
- web_search: Search general web sources for technical and current information.
- documentation_search: Search official technical documentation and developer guides.
- document_reader: Read, extract, and analyze text from uploaded documents.

Always respond in strictly valid JSON without explanation or formatting text.
"""

USER_PROMPT_TEMPLATE = """Analyze the following agent build request and extract structured requirements:

Agent Name: {agent_name}
Description: {description}
Objective: {objective}
Caller-Suggested Tools: {suggested_tools}
User Constraints: {constraints}
{research_context_section}

Return a single JSON object with the following exact keys:
{{
  "objective": "A clear, concise 1-2 sentence statement of what the agent accomplishes.",
  "capabilities": ["List of distinct capabilities required, e.g. search repositories, parse papers, extract document tables"],
  "constraints": ["List of operational and behavioral constraints"],
  "suggested_tools": ["List of approved tool names selected from: github_search, paper_search, web_search, documentation_search, document_reader"]
}}
"""

RESEARCH_CONTEXT_TEMPLATE = """
Research Context Provided:
- Research Summary: {research_summary}
- Key Findings: {key_findings}
- Recommended Approach: {recommended_approach}
Use these research insights to enrich the agent objective, capabilities, and tool selection.
"""
