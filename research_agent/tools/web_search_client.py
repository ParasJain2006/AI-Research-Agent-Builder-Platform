"""Web search client using DuckDuckGo Instant Answer API.
Returns a small list of search result objects with title, URL and snippet.
No API key required.
"""

from typing import List, Dict, Any
import httpx
import urllib.parse

class WebResult:
    def __init__(self, title: str, url: str, snippet: str):
        self.title = title
        self.url = url
        self.snippet = snippet

async def search_web(query: str, limit: int = 5) -> List[WebResult]:
    # DuckDuckGo instant answer returns many results; we take the first `limit`.
    params = {
        "q": query,
        "format": "json",
        "no_redirect": 1,
        "no_html": 1,
        "skip_disambiguation": 1,
    }
    url = f"https://api.duckduckgo.com/?{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        results: List[WebResult] = []
        for rel in data.get("RelatedTopics", [])[:limit]:
            if "Text" in rel and "FirstURL" in rel:
                results.append(WebResult(title=rel.get("Text", ""), url=rel["FirstURL"], snippet=""))
        return results
