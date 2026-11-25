"""Command‑line interface for the Research Agent.
Usage:
    python -m research_agent.cli "your query here"
"""

import sys
import asyncio
from .service import run_research
from ..shared.schemas.research import ResearchRequest

async def _main():
    if len(sys.argv) < 2:
        print("Usage: python -m research_agent.cli \"query\"")
        sys.exit(1)
    query = sys.argv[1]
    request = ResearchRequest(
        session_id="cli-session",
        query=query,
        source_types=["github", "paper", "web"],
        max_sources=15,
        user_constraints=[],
    )
    result = await run_research(request)
    print(result.json(indent=2))

if __name__ == "__main__":
    asyncio.run(_main())
