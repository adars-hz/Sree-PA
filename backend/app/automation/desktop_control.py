"""
Desktop Control Engine for Project SREE
Provides complete OS keyboard, mouse, window, and desktop automation via PyAutoGUI and Win32.
"""

import os
import time
import ctypes
import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    import pyautogui
    # PyAutoGUI Safety configuration
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.03
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    pyautogui = None
    PYAUTOGUI_AVAILABLE = False

logger = logging.getLogger("sree.desktop_control")
if not PYAUTOGUI_AVAILABLE:
    logger.warning("PyAutoGUI unavailable or display cannot be opened. Desktop automation running in fallback mode.")

# Windows Multi-Monitor Win32 Structures
class _RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]

class _MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('rcMonitor', _RECT),
        ('rcWork', _RECT),
        ('dwFlags', ctypes.c_ulong),
        ('szDevice', ctypes.c_wchar * 32)
    ]

class DesktopControlEngine:
    def __init__(self):
        self.active_monitor_index: int = 0
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                self.screen_width, self.screen_height = pyautogui.size()
            except Exception:
                self.screen_width, self.screen_height = (1920, 1080)
        else:
            self.screen_width, self.screen_height = (1920, 1080)

    # --- Multi-Monitor Enumeration & Coordinate Normalization ---
    def get_monitors(self) -> List[Dict[str, Any]]:
        """
        Enumerates all physical and virtual connected display monitors.
        Uses native Win32 EnumDisplayMonitors on Windows with graceful cross-platform fallback.
        """
        monitors: List[Dict[str, Any]] = []
        if os.name == "nt":
            try:
                def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                    info = _MONITORINFOEX()
                    info.cbSize = ctypes.sizeof(_MONITORINFOEX)
                    if ctypes.windll.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info)):
                        r = info.rcMonitor
                        is_primary = bool(info.dwFlags & 1)
                        clean_name = str(info.szDevice).replace("\\\\.\\", "").strip() or f"DISPLAY{len(monitors)+1}"
                        monitors.append({
                            "index": len(monitors),
                            "name": clean_name,
                            "device": str(info.szDevice),
                            "left": int(r.left),
                            "top": int(r.top),
                            "right": int(r.right),
                            "bottom": int(r.bottom),
                            "width": int(r.right - r.left),
                            "height": int(r.bottom - r.top),
                            "is_primary": is_primary
                        })
                    return True

                MONITORENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(_RECT), ctypes.c_longlong)
                callback = MONITORENUMPROC(monitor_enum_proc)
                ctypes.windll.user32.EnumDisplayMonitors(None, None, callback, 0)
            except Exception as e:
                logger.warning(f"Error enumerating monitors via Win32: {e}")

        if not monitors:
            monitors.append({
                "index": 0,
                "name": "DISPLAY1",
                "device": "\\\\.\\DISPLAY1",
                "left": 0,
                "top": 0,
                "right": self.screen_width,
                "bottom": self.screen_height,
                "width": self.screen_width,
                "height": self.screen_height,
                "is_primary": True
            })
        return monitors

    def get_virtual_screen_geometry(self) -> Dict[str, Any]:
        """Calculates bounding box and dimensions spanning all connected monitors."""
        monitors = self.get_monitors()
        min_left = min(m["left"] for m in monitors)
        min_top = min(m["top"] for m in monitors)
        max_right = max(m["right"] for m in monitors)
        max_bottom = max(m["bottom"] for m in monitors)
        return {
            "left": min_left,
            "top": min_top,
            "right": max_right,
            "bottom": max_bottom,
            "width": max_right - min_left,
            "height": max_bottom - min_top,
            "monitor_count": len(monitors)
        }

    def set_active_monitor(self, monitor_index: int) -> Dict[str, Any]:
        """Sets the active display monitor index for targeted clicks and screen controls."""
        monitors = self.get_monitors()
        if 0 <= monitor_index < len(monitors):
            self.active_monitor_index = monitor_index
            return {
                "success": True,
                "active_monitor_index": self.active_monitor_index,
                "monitor": monitors[self.active_monitor_index]
            }
        return {
            "success": False,
            "error": f"Invalid monitor index: {monitor_index}. Total monitors: {len(monitors)}",
            "active_monitor_index": self.active_monitor_index
        }

    def get_active_monitor(self) -> Dict[str, Any]:
        """Retrieves details of the currently selected target monitor."""
        monitors = self.get_monitors()
        if 0 <= self.active_monitor_index < len(monitors):
            return monitors[self.active_monitor_index]
        return monitors[0]

    def normalize_coordinates(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None
    ) -> Tuple[int, int]:
        """
        Normalizes coordinates across multi-monitor displays:
        1. If x_ratio and y_ratio (0.0 to 1.0) are given, scales them relative to the target monitor bounds.
        2. If monitor_index is provided with (x, y), offsets relative to that monitor's (left, top).
        3. If raw (x, y) is provided, clamps safely within the global multi-monitor virtual screen.
        """
        monitors = self.get_monitors()
        target_idx = monitor_index if monitor_index is not None else self.active_monitor_index
        if target_idx < 0 or target_idx >= len(monitors):
            target_idx = 0
        target_mon = monitors[target_idx]

        # 1. Ratio-based normalized coordinates (e.g. from PWA touchscreen or UI viewport clicks)
        if x_ratio is not None and y_ratio is not None:
            clamped_rx = max(0.0, min(1.0, float(x_ratio)))
            clamped_ry = max(0.0, min(1.0, float(y_ratio)))
            abs_x = int(target_mon["left"] + (clamped_rx * target_mon["width"]))
            abs_y = int(target_mon["top"] + (clamped_ry * target_mon["height"]))
            final_x = max(target_mon["left"], min(target_mon["right"] - 1, abs_x))
            final_y = max(target_mon["top"], min(target_mon["bottom"] - 1, abs_y))
            return final_x, final_y

        # 2. Monitor-relative pixel coordinates
        if monitor_index is not None and x is not None and y is not None:
            abs_x = target_mon["left"] + x
            abs_y = target_mon["top"] + y
            final_x = max(target_mon["left"], min(target_mon["right"] - 1, abs_x))
            final_y = max(target_mon["top"], min(target_mon["bottom"] - 1, abs_y))
            return final_x, final_y

        # 3. Raw global coordinates: clamp to virtual multi-monitor bounding box
        virt = self.get_virtual_screen_geometry()
        raw_x = x if x is not None else target_mon["left"]
        raw_y = y if y is not None else target_mon["top"]
        final_x = max(virt["left"], min(virt["right"] - 1, raw_x))
        final_y = max(virt["top"], min(virt["bottom"] - 1, raw_y))
        return final_x, final_y

    def get_screen_dimensions(self) -> Tuple[int, int]:
        active_mon = self.get_active_monitor()
        return active_mon["width"], active_mon["height"]

    def get_cursor_position(self) -> Tuple[int, int]:
        if PYAUTOGUI_AVAILABLE and pyautogui is not None:
            try:
                point = pyautogui.position()
                return point.x, point.y
            except Exception:
                return (0, 0)
        return (0, 0)

    # --- Mouse Control ---
    def move_mouse(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None,
        duration: float = 0.1
    ) -> Dict[str, Any]:
        """Moves cursor to target (x, y) or normalized coordinates across any monitor."""
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return {"success": False, "error": "PyAutoGUI is not available in this environment."}
        try:
            target_x, target_y = self.normalize_coordinates(
                x=x, y=y, x_ratio=x_ratio, y_ratio=y_ratio, monitor_index=monitor_index
            )
            pyautogui.moveTo(target_x, target_y, duration=duration)
            return {
                "success": True,
                "x": target_x,
                "y": target_y,
                "monitor_index": monitor_index if monitor_index is not None else self.active_monitor_index
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None,
        button: str = "left",
        clicks: int = 1
    ) -> Dict[str, Any]:
        """Performs single or double click at coordinates or normalized ratios across any monitor."""
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return {"success": False, "error": "PyAutoGUI is not available in this environment."}
        try:
            if (x is not None and y is not None) or (x_ratio is not None and y_ratio is not None):
                self.move_mouse(x=x, y=y, x_ratio=x_ratio, y_ratio=y_ratio, monitor_index=monitor_index, duration=0.0)
            pyautogui.click(button=button, clicks=clicks)
            cx, cy = self.get_cursor_position()
            return {
                "success": True,
                "action": f"{button}_click",
                "clicks": clicks,
                "x": cx,
                "y": cy,
                "monitor_index": monitor_index if monitor_index is not None else self.active_monitor_index
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def double_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.click(x=x, y=y, x_ratio=x_ratio, y_ratio=y_ratio, monitor_index=monitor_index, button="left", clicks=2)

    def right_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None
    ) -> Dict[str, Any]:
        return self.click(x=x, y=y, x_ratio=x_ratio, y_ratio=y_ratio, monitor_index=monitor_index, button="right", clicks=1)

    def scroll(self, clicks: int = -3) -> Dict[str, Any]:
        """Scrolls up (positive) or down (negative)."""
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return {"success": False, "error": "PyAutoGUI is not available in this environment."}
        try:
            pyautogui.scroll(clicks)
            return {"success": True, "scrolled": clicks}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def drag_to(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        x_ratio: Optional[float] = None,
        y_ratio: Optional[float] = None,
        monitor_index: Optional[int] = None,
        duration: float = 0.3
    ) -> Dict[str, Any]:
        """Drags mouse to target position holding left button across any monitor."""
        if not PYAUTOGUI_AVAILABLE or pyautogui is None:
            return {"success": False, "error": "PyAutoGUI is not available in this environment."}
        try:
            target_x, target_y = self.normalize_coordinates(
                x=x, y=y, x_ratio=x_ratio, y_ratio=y_ratio, monitor_index=monitor_index
            )
            pyautogui.dragTo(target_x, target_y, duration=duration, button="left")
            return {
                "success": True,
                "dragged_to": (target_x, target_y),
                "monitor_index": monitor_index if monitor_index is not None else self.active_monitor_index
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Keyboard Control ---
    def type_text(self, text: str, interval: float = 0.02) -> Dict[str, Any]:
        """Types string into active window."""
        try:
            pyautogui.write(text, interval=interval)
            return {"success": True, "typed_length": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key_name: str) -> Dict[str, Any]:
        """Presses an individual key (e.g. 'enter', 'esc', 'tab', 'space', 'backspace')."""
        try:
            key_clean = key_name.lower().strip()
            pyautogui.press(key_clean)
            return {"success": True, "pressed_key": key_clean}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def hotkey(self, *keys: str) -> Dict[str, Any]:
        """Executes a key combo (e.g. ['ctrl', 'c'], ['alt', 'tab'], ['win', 'd'])."""
        try:
            cleaned_keys = [k.lower().strip() for k in keys if k]
            pyautogui.hotkey(*cleaned_keys)
            return {"success": True, "hotkey": "+".join(cleaned_keys)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Windows System Shortcuts ---
    def execute_system_action(self, action_name: str) -> Dict[str, Any]:
        """Executes standard desktop management actions."""
        act = action_name.lower().strip().replace(" ", "_")
        try:
            if act in ("minimize_all", "show_desktop", "desktop"):
                pyautogui.hotkey("win", "d")
                return {"success": True, "action": "show_desktop", "message": "Minimized all windows."}

            if act in ("switch_window", "alt_tab"):
                pyautogui.hotkey("alt", "tab")
                return {"success": True, "action": "switch_window", "message": "Switched active window."}

            if act in ("task_manager", "taskmgr"):
                pyautogui.hotkey("ctrl", "shift", "esc")
                return {"success": True, "action": "task_manager", "message": "Opened Task Manager."}

            if act in ("close_window", "close_app"):
                pyautogui.hotkey("alt", "f4")
                return {"success": True, "action": "close_window", "message": "Closed active window."}

            if act in ("volume_up", "vol_up"):
                pyautogui.press("volumeup")
                return {"success": True, "action": "volume_up", "message": "Volume increased."}

            if act in ("volume_down", "vol_down"):
                pyautogui.press("volumedown")
                return {"success": True, "action": "volume_down", "message": "Volume decreased."}

            if act in ("mute", "volume_mute"):
                pyautogui.press("volumemute")
                return {"success": True, "action": "volume_mute", "message": "Muted audio."}

            if act in ("copy", "copy_text"):
                pyautogui.hotkey("ctrl", "c")
                return {"success": True, "action": "copy", "message": "Copied selection."}

            if act in ("paste", "paste_text"):
                pyautogui.hotkey("ctrl", "v")
                return {"success": True, "action": "paste", "message": "Pasted clipboard content."}

            if act in ("lock_pc", "lock_screen"):
                ctypes.windll.user32.LockWorkStation()
                return {"success": True, "action": "lock_pc", "message": "Windows workstation locked."}

            return {"success": False, "error": f"Unknown system action: {action_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

desktop_control = DesktopControlEngine()
