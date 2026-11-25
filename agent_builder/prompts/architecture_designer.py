"""
agent_builder.prompts.architecture_designer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Prompts for designing workflow nodes and edges for an agent definition.
"""

SYSTEM_PROMPT = """You are an expert AI workflow designer.
Your task is to design a clean, modular workflow graph of 2 to 4 nodes with directed edges.

Workflow rules:
1. Every node must have:
   - "node_id": a short snake_case name (e.g. "search_sources", "extract_evidence", "synthesize_findings")
   - "node_type": a type label (e.g. "search", "extract", "compare", "synthesize", "qna")
   - "description": clear explanation of this node's task
   - "allowed_tools": list of tool names this node uses (must be a subset of the agent's selected tools)
2. Every edge must connect a source_node to a target_node.
3. Every node in workflow_nodes must be reachable from the "entry_node".
4. Do not create disconnected islands.
5. Keep the workflow purposeful, simple, and linear or single-branching.

Respond in strictly valid JSON format without markdown fences or additional commentary.
"""

USER_PROMPT_TEMPLATE = """Design a workflow graph for the following agent:

Agent Name: {agent_name}
Objective: {objective}
Capabilities: {capabilities}
Selected Tools: {selected_tools}

Return a single JSON object with the following structure:
{{
  "entry_node": "first_node_id",
  "workflow_nodes": [
    {{
      "node_id": "first_node_id",
      "node_type": "search",
      "description": "Performs initial queries",
      "allowed_tools": ["tool_1"]
    }},
    {{
      "node_id": "second_node_id",
      "node_type": "synthesize",
      "description": "Processes results",
      "allowed_tools": []
    }}
  ],
  "workflow_edges": [
    {{
      "source_node": "first_node_id",
      "target_node": "second_node_id",
      "condition": null
    }}
  ]
}}
"""
