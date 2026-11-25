"""Wikipedia client for simple opensearch queries.
Returns a list of title/url/snippet triples.
"""

from typing import List, Dict, Any
import httpx

class WikipediaResult:
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

async def search_wikipedia(query: str, limit: int = 5) -> List[WikipediaResult]:
    params = {
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json",
        "origin": "*",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get("https://en.wikipedia.org/w/api.php?action=opensearch", params=params)
        resp.raise_for_status()
        data = resp.json()
        titles: List[str] = data[1]
        urls: List[str] = data[3]
        # Wikipedia opensearch does not return snippets; we issue a second request for extracts if needed.
        # For simplicity we return empty snippets.
        results: List[WikipediaResult] = []
        for t, u in zip(titles, urls):
            results.append(WikipediaResult(title=t, url=u, snippet=""))
        return results
