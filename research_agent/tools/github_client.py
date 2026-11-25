"""GitHub client for repo search.
Implements a simple async search using the GitHub REST API.
Handles optional token authentication, rate‑limit back‑off, and normalizes
responses into a lightweight data class.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

# Simple data model for a repository result
class GitHubRepo(BaseModel):
    name: str
    html_url: str = Field(..., alias="url")
    description: Optional[str]
    stargazers_count: int = Field(..., alias="stars")
    forks_count: int = Field(..., alias="forks")
    language: Optional[str]
    topics: List[str] = Field(default_factory=list)
    updated_at: str
    # additional raw payload for later use if needed
    raw: Dict[str, Any] = Field(default_factory=dict)


class GitHubClient:
    BASE_URL = "https://api.github.com"
    SEARCH_ENDPOINT = "/search/repositories"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
            resp = await client.get(self.BASE_URL + self.SEARCH_ENDPOINT, params=params)
            # Basic rate‑limit handling – if we are rate‑limited, wait and retry once
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = int(resp.headers.get("X-RateLimit-Reset", "0"))
                wait_seconds = max(reset - int(asyncio.time.time()), 1)
                await asyncio.sleep(wait_seconds)
                resp = await client.get(self.BASE_URL + self.SEARCH_ENDPOINT, params=params)
            resp.raise_for_status()
            return resp.json()

    async def search_repos(self, query: str, limit: int = 10) -> List[GitHubRepo]:
        """Search GitHub repositories.
        Returns up to `limit` results (already sorted by GitHub relevance).
        """
        params = {
            "q": query,
            "per_page": min(limit, 100),
            "sort": "stars",
            "order": "desc",
        }
        data = await self._request(params)
        items = data.get("items", [])[:limit]
        results: List[GitHubRepo] = []
        for item in items:
            repo = GitHubRepo(
                name=item.get("full_name"),
                url=item.get("html_url"),
                description=item.get("description"),
                stars=item.get("stargazers_count"),
                forks=item.get("forks_count"),
                language=item.get("language"),
                topics=item.get("topics", []),
                updated_at=item.get("updated_at"),
                raw=item,
            )
            results.append(repo)
        return results
