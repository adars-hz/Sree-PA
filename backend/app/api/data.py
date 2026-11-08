"""
Data Export and Privacy Erasure API Endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from ..database.db import db_manager

router = APIRouter(prefix="/api/data", tags=["Privacy & Data"])

class WipeRequest(BaseModel):
    confirm: bool = Field(..., description="Must be set to true to proceed with full data wipe")

@router.get("/export")
async def export_personal_data():
    """
    Exports all personal notes, memories, reminders, and conversations as a JSON file.
    """
    data = db_manager.export_all_data()
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=sree_personal_data_export.json"}
    )

@router.post("/wipe")
async def wipe_all_data(request: WipeRequest):
    """
    Permanently erases all local database records.
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required. Set 'confirm: true' to proceed.")

    db_manager.wipe_all_data()
    return {
        "status": "success",
        "message": "All personal memories, notes, reminders, and conversation records have been permanently erased."
    }

