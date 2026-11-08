"""
Desktop Screen Sharing & Remote Control API Endpoints
Provides real-time MJPEG desktop streaming, screen capture, mouse, keyboard, and OS commands.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..automation.screen_share import screen_share
from ..automation.desktop_control import desktop_control

router = APIRouter(prefix="/api/desktop", tags=["Desktop Control & Screen Share"])

class FrameUploadRequest(BaseModel):
    frame_base64: str = Field(..., description="Base64 encoded JPEG/PNG frame from screen capture")

class MouseControlRequest(BaseModel):
    action: str = Field("click", description="'move', 'click', 'double_click', 'right_click', 'scroll', 'drag'")
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = "left"
    clicks: Optional[int] = 1

class KeyboardControlRequest(BaseModel):
    action: str = Field("type", description="'type', 'press', 'hotkey'")
    text: Optional[str] = None
    key: Optional[str] = None
    keys: Optional[List[str]] = None

class SystemActionRequest(BaseModel):
    action: str = Field(..., description="'minimize_all', 'switch_window', 'task_manager', 'close_window', 'volume_up', 'volume_down', 'mute', 'copy', 'paste', 'lock_pc'")

@router.get("/status")
def get_desktop_status() -> Dict[str, Any]:
    """Returns screen dimensions, cursor position, and screen share stream status."""
    w, h = desktop_control.get_screen_dimensions()
    cx, cy = desktop_control.get_cursor_position()
    share_status = screen_share.get_status()
    return {
        "screen": {"width": w, "height": h},
        "cursor": {"x": cx, "y": cy},
        "stream": share_status
    }

@router.get("/stream")
async def stream_desktop_screen():
    """
    Live multipart MJPEG desktop video stream.
    Can be embedded directly into <img src="/api/desktop/stream"> on Android or desktop browsers.
    """
    return StreamingResponse(
        screen_share.generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/snapshot")
def get_screen_snapshot():
    """Returns the latest screen frame as raw JPEG bytes."""
    data = screen_share.get_latest_frame_bytes()
    return Response(content=data, media_type="image/jpeg")

@router.post("/frame")
def upload_screen_frame(req: FrameUploadRequest) -> Dict[str, Any]:
    """Receives screen capture frames from host display media."""
    ok = screen_share.update_frame_from_base64(req.frame_base64)
    return {"success": ok}

@router.post("/screenshot/save")
def save_screenshot_file(filename: Optional[str] = None) -> Dict[str, Any]:
    """Saves the current desktop screen to user Pictures or Desktop folder."""
    return screen_share.save_screenshot_to_disk(filename)

@router.post("/mouse")
def control_mouse(req: MouseControlRequest) -> Dict[str, Any]:
    """Executes mouse move, click, or scroll command."""
    act = req.action.lower()
    if act == "move":
        return desktop_control.move_mouse(req.x or 0, req.y or 0)
    elif act in ("click", "left_click"):
        return desktop_control.click(req.x, req.y, button=req.button or "left", clicks=req.clicks or 1)
    elif act == "double_click":
        return desktop_control.double_click(req.x, req.y)
    elif act == "right_click":
        return desktop_control.right_click(req.x, req.y)
    elif act == "scroll":
        return desktop_control.scroll(clicks=req.clicks or -3)
    elif act == "drag":
        return desktop_control.drag_to(req.x or 0, req.y or 0)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mouse action: {req.action}")

@router.post("/keyboard")
def control_keyboard(req: KeyboardControlRequest) -> Dict[str, Any]:
    """Executes typing or keystroke shortcuts."""
    act = req.action.lower()
    if act == "type":
        if not req.text:
            raise HTTPException(status_code=400, detail="Missing 'text' field for typing.")
        return desktop_control.type_text(req.text)
    elif act == "press":
        if not req.key:
            raise HTTPException(status_code=400, detail="Missing 'key' field.")
        return desktop_control.press_key(req.key)
    elif act == "hotkey":
        if not req.keys:
            raise HTTPException(status_code=400, detail="Missing 'keys' list for shortcut.")
        return desktop_control.hotkey(*req.keys)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported keyboard action: {req.action}")

@router.post("/action")
def execute_os_action(req: SystemActionRequest) -> Dict[str, Any]:
    """Executes high-level desktop management command."""
    return desktop_control.execute_system_action(req.action)

