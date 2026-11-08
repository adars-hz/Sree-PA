"""
Notes Management API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database.db import db_manager

router = APIRouter(prefix="/api/notes", tags=["Notes"])

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    tags: Optional[str] = ""

class NoteUpdate(BaseModel):
    title: str
    content: str
    tags: Optional[str] = ""

@router.get("")
async def list_notes(search: Optional[str] = Query(None)):
    notes = db_manager.get_notes(search=search)
    return {"notes": notes}

@router.post("")
async def create_note(note: NoteCreate):
    note_id = db_manager.create_note(title=note.title, content=note.content, tags=note.tags or "")
    return {"status": "success", "id": note_id, "message": "Note created"}

@router.put("/{note_id}")
async def update_note(note_id: int, note: NoteUpdate):
    success = db_manager.update_note(note_id=note_id, title=note.title, content=note.content, tags=note.tags or "")
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success", "message": "Note updated"}

@router.delete("/{note_id}")
async def delete_note(note_id: int):
    success = db_manager.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success", "message": "Note deleted"}

