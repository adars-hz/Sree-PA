"""
Memory Management API Endpoints
Provides endpoints for memory retrieval, creation, deletion,
offline semantic vector search, and local embedding reindexing.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database.db import db_manager
from ..memory.manager import memory_manager

router = APIRouter(prefix="/api/memory", tags=["Memory"])

class MemoryCreate(BaseModel):
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    category: Optional[str] = "general"

@router.get("")
async def get_memories():
    return {"memories": db_manager.get_all_memories(approved_only=False)}

@router.get("/search")
async def search_memories(
    query: str = Query(..., min_length=1, description="Semantic search query"),
    top_k: int = Query(default=5, ge=1, le=50, description="Max memories to return"),
    threshold: float = Query(default=0.20, ge=0.0, le=1.0, description="Minimum cosine similarity threshold")
):
    """
    Search memories using 100% offline local vector embeddings and cosine similarity.
    Retrieves conceptually related memories (e.g. 'coding tools' -> 'Editor: VSCode').
    """
    results = memory_manager.search_semantic_memories(
        query=query,
        top_k=top_k,
        min_similarity=threshold
    )
    return {
        "query": query,
        "count": len(results),
        "results": results
    }

@router.post("/reindex")
async def reindex_memories():
    """
    Computes vector embeddings for all stored memories lacking embeddings.
    Ensures 100% vector indexing across legacy and new memories.
    """
    count = memory_manager.reindex_all_memories()
    return {
        "status": "success",
        "reindexed_count": count,
        "message": f"Successfully reindexed {count} memories with local vector embeddings."
    }

@router.post("")
async def add_memory(item: MemoryCreate):
    mem_id = memory_manager.add_memory(key=item.key, value=item.value, category=item.category)
    return {"status": "success", "id": mem_id, "message": f"Memory saved: {item.key}"}

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    success = db_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "message": "Memory deleted"}
