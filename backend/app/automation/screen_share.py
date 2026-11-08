"""
Desktop Screen Sharing & Streaming Engine for Project SREE
Enables live MJPEG desktop video streaming, remote snapshot inspection,
and vision analysis for AI reasoning.
"""

import io
import time
import base64
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator

from PIL import Image
from .path_resolver import dynamic_path_resolver

logger = logging.getLogger("sree.screen_share")

class ScreenShareEngine:
    def __init__(self):
        self._latest_jpeg_bytes: Optional[bytes] = None
        self._last_frame_timestamp: float = 0
        self._is_sharing_active: bool = False
        self._subscribers: int = 0
        self._create_placeholder_frame()

    def _create_placeholder_frame(self):
        """Generates a default dark standby frame when no capture is active."""
        img = Image.new("RGB", (1280, 720), color=(10, 15, 30))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        self._latest_jpeg_bytes = buf.getvalue()
        self._last_frame_timestamp = time.time()

    def update_frame_from_base64(self, b64_data: str) -> bool:
        """Pushes a new frame captured from the desktop browser / PWA screen capture stream."""
        try:
            if "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            raw = base64.b64decode(b64_data)
            self._latest_jpeg_bytes = raw
            self._last_frame_timestamp = time.time()
            self._is_sharing_active = True
            return True
        except Exception as e:
            logger.error(f"Failed to update frame: {e}")
            return False

    def update_frame_from_bytes(self, jpeg_bytes: bytes) -> bool:
        self._latest_jpeg_bytes = jpeg_bytes
        self._last_frame_timestamp = time.time()
        self._is_sharing_active = True
        return True

    def get_latest_frame_bytes(self) -> bytes:
        return self._latest_jpeg_bytes or b""

    def get_latest_frame_base64(self) -> str:
        if self._latest_jpeg_bytes:
            return base64.b64encode(self._latest_jpeg_bytes).decode("ascii")
        return ""

    def save_screenshot_to_disk(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Saves current desktop capture to user's Pictures or Desktop folder."""
        try:
            name = filename or f"SREE_Screenshot_{int(time.time())}.jpg"
            dest_folder = dynamic_path_resolver.get_pictures()
            if not dest_folder.exists():
                dest_folder = dynamic_path_resolver.get_desktop()

            dest_path = dest_folder / name
            with open(dest_path, "wb") as f:
                f.write(self._latest_jpeg_bytes)

            return {
                "success": True,
                "path": str(dest_path),
                "filename": name,
                "message": f"Saved screenshot to {dest_path.name}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_mjpeg_stream(self) -> AsyncGenerator[bytes, None]:
        """Yields multipart MJPEG stream for real-time video playback in browsers and mobile phones."""
        self._subscribers += 1
        try:
            while True:
                frame = self.get_latest_frame_bytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
                # Stream at ~15-20 FPS for smooth remote screen viewing
                await asyncio.sleep(0.065)
        except asyncio.CancelledError:
            pass
        finally:
            self._subscribers = max(0, self._subscribers - 1)

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self._is_sharing_active,
            "subscribers": self._subscribers,
            "last_frame_age_seconds": round(time.time() - self._last_frame_timestamp, 1) if self._last_frame_timestamp else None,
            "frame_size_bytes": len(self._latest_jpeg_bytes) if self._latest_jpeg_bytes else 0
        }

screen_share = ScreenShareEngine()
