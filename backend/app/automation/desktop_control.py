"""
Desktop Control Engine for Project SREE
Provides complete OS keyboard, mouse, window, and desktop automation via PyAutoGUI and Win32.
"""

import os
import time
import ctypes
import logging
from typing import Dict, Any, List, Optional, Tuple

import pyautogui

logger = logging.getLogger("sree.desktop_control")

# PyAutoGUI Safety configuration
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.03

class DesktopControlEngine:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    def get_screen_dimensions(self) -> Tuple[int, int]:
        self.screen_width, self.screen_height = pyautogui.size()
        return self.screen_width, self.screen_height

    def get_cursor_position(self) -> Tuple[int, int]:
        point = pyautogui.position()
        return point.x, point.y

    # --- Mouse Control ---
    def move_mouse(self, x: int, y: int, duration: float = 0.1) -> Dict[str, Any]:
        """Moves cursor to target (x, y) coordinates."""
        try:
            clamped_x = max(0, min(self.screen_width - 1, x))
            clamped_y = max(0, min(self.screen_height - 1, y))
            pyautogui.moveTo(clamped_x, clamped_y, duration=duration)
            return {"success": True, "x": clamped_x, "y": clamped_y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        """Performs single or double click at coordinates (or current position)."""
        try:
            if x is not None and y is not None:
                self.move_mouse(x, y, duration=0.0)
            pyautogui.click(button=button, clicks=clicks)
            return {"success": True, "action": f"{button}_click", "clicks": clicks}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        return self.click(x=x, y=y, button="left", clicks=2)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        return self.click(x=x, y=y, button="right", clicks=1)

    def scroll(self, clicks: int = -3) -> Dict[str, Any]:
        """Scrolls up (positive) or down (negative)."""
        try:
            pyautogui.scroll(clicks)
            return {"success": True, "scrolled": clicks}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def drag_to(self, x: int, y: int, duration: float = 0.3) -> Dict[str, Any]:
        """Drags mouse to target position holding left button."""
        try:
            pyautogui.dragTo(x, y, duration=duration, button="left")
            return {"success": True, "dragged_to": (x, y)}
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
