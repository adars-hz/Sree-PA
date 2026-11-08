"""
Free Web Search API Endpoint for Project SREE
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import List, Dict
from ..services.search import web_search_service

router = APIRouter(prefix="/api/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Web search query")
    max_results: int = Field(default=5, ge=1, le=10)

@router.get("")
async def search_get(q: str = Query(..., min_length=2)):
    results = await web_search_service.search(q)
    return {"query": q, "results": results, "source": "DuckDuckGo Live Search"}

@router.post("")
async def search_post(request: SearchRequest):
    results = await web_search_service.search(request.query, max_results=request.max_results)
    return {"query": request.query, "results": results, "source": "DuckDuckGo Live Search"}

