import os
import sys
import asyncio
from pathlib import Path

# Ensure repo root is on path
repo_root = Path(__file__).resolve().parents[2]
sys.path.append(str(repo_root))

from research_agent.service import run_research
from shared.schemas.research import ResearchRequest

async def main():
    req = ResearchRequest(
        session_id='live-test',
        query='Compare LangGraph and CrewAI for building a multi-agent coding assistant',
        source_types=['github','paper','web'],
        max_sources=10,
        user_constraints=[],
    )
    result = await run_research(req)
    print(result.json(indent=2))

if __name__ == '__main__':
    asyncio.run(main())
