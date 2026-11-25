"""Paper client for Semantic Scholar.
Implements async search returning a small normalized model.
"""

import os
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field

class PaperInfo(BaseModel):
    paper_id: str = Field(..., alias="paperId")
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str]
    year: Optional[int]
    citation_count: Optional[int]
    url: Optional[str]
    raw: Dict[str, Any] = Field(default_factory=dict)

class PaperClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    SEARCH_ENDPOINT = "/paper/search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {"Accept": "application/json"}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    async def search_papers(self, query: str, limit: int = 10) -> List[PaperInfo]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,abstract,year,citationCount,url",
        }
        async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
            resp = await client.get(self.BASE_URL + self.SEARCH_ENDPOINT, params=params)
            resp.raise_for_status()
            data = resp.json()
            papers: List[PaperInfo] = []
            for item in data.get("data", [])[:limit]:
                paper = PaperInfo(
                    paperId=item.get("paperId"),
                    title=item.get("title", ""),
                    authors=[a.get("name") for a in item.get("authors", []) if a.get("name")],
                    abstract=item.get("abstract"),
                    year=item.get("year"),
                    citationCount=item.get("citationCount"),
                    url=item.get("url"),
                    raw=item,
                )
                papers.append(paper)
            return papers
