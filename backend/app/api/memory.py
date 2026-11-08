"""
Memory Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database.db import db_manager

router = APIRouter(prefix="/api/memory", tags=["Memory"])

class MemoryCreate(BaseModel):
    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    category: Optional[str] = "general"

@router.get("")
async def get_memories():
    return {"memories": db_manager.get_all_memories(approved_only=False)}

@router.post("")
async def add_memory(item: MemoryCreate):
    mem_id = db_manager.add_memory(key=item.key, value=item.value, category=item.category)
    return {"status": "success", "id": mem_id, "message": f"Memory saved: {item.key}"}

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    success = db_manager.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "success", "message": "Memory deleted"}

