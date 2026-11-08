"""
Laptop Automation & Device Control API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from ..automation.executor import automation_executor

router = APIRouter(prefix="/api/automation", tags=["Automation"])

class LaunchRequest(BaseModel):
    app_id: str = Field(..., description="ID of allowlisted app, e.g. 'notepad', 'calculator'")

class FileSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Filename or keyword")

class FileReadRequest(BaseModel):
    file_path: str = Field(..., description="Path to file within approved directories")

@router.get("/apps")
async def list_allowed_apps():
    """List all pre-authorized applications."""
    return {"apps": automation_executor.get_available_apps()}

@router.post("/launch")
async def launch_app(request: LaunchRequest):
    """Launch an allowlisted application safely."""
    result = automation_executor.launch_application(request.app_id)
    if not result["success"]:
        raise HTTPException(status_code=403, detail=result["error"])
    return result

@router.get("/telemetry")
async def get_device_telemetry():
    """Get battery, uptime, and system status."""
    return automation_executor.get_system_telemetry()

@router.post("/files/search")
async def search_files(request: FileSearchRequest):
    """Search for files strictly in approved directories."""
    results = automation_executor.search_approved_files(request.query)
    return {"results": results, "count": len(results)}

@router.post("/files/read")
async def read_file(request: FileReadRequest):
    """Read a document within approved directories."""
    result = automation_executor.read_approved_text_file(request.file_path)
    if not result["success"]:
        raise HTTPException(status_code=403, detail=result["error"])
    return result

