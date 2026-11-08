"""
Reminders and Task Management API Endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database.db import db_manager

router = APIRouter(prefix="/api/reminders", tags=["Reminders"])

class ReminderCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    due_time: Optional[str] = ""
    priority: Optional[str] = "normal"

class ToggleReminder(BaseModel):
    completed: bool

@router.get("")
async def list_reminders():
    reminders = db_manager.get_reminders(include_completed=True)
    return {"reminders": reminders}

@router.post("")
async def create_reminder(item: ReminderCreate):
    reminder_id = db_manager.create_reminder(
        title=item.title,
        description=item.description or "",
        due_time=item.due_time or "",
        priority=item.priority or "normal"
    )
    return {"status": "success", "id": reminder_id, "message": "Reminder created"}

@router.patch("/{reminder_id}/toggle")
async def toggle_reminder_status(reminder_id: int, payload: ToggleReminder):
    success = db_manager.toggle_reminder(reminder_id, payload.completed)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": "Reminder updated"}

@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: int):
    success = db_manager.delete_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": "Reminder deleted"}

