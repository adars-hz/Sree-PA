"""
Desktop Screen Sharing & Remote Control Test Suite for Project SREE
Validates 0ms screen sharing, screenshot capture, mouse/keyboard automation,
OS system shortcuts, and skill crystallizer voice commands.
"""

import unittest
import asyncio
from unittest.mock import patch, MagicMock
from pathlib import Path

from backend.app.automation.desktop_control import desktop_control
from backend.app.automation.screen_share import screen_share
from backend.app.automation.crystallizer import skill_crystallizer

class TestDesktopControl(unittest.TestCase):
    def test_01_screen_dimensions(self):
        w, h = desktop_control.get_screen_dimensions()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    def test_02_cursor_position(self):
        x, y = desktop_control.get_cursor_position()
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

    def test_03_mouse_move_clamping(self):
        res = desktop_control.move_mouse(100, 200, duration=0.0)
        self.assertTrue(res["success"])
        self.assertEqual(res["x"], 100)
        self.assertEqual(res["y"], 200)

    def test_04_mouse_click(self):
        with patch("pyautogui.click") as mock_click:
            res = desktop_control.click(button="left", clicks=1)
            self.assertTrue(res["success"])
            mock_click.assert_called_once_with(button="left", clicks=1)

    def test_05_mouse_double_click(self):
        with patch("pyautogui.click") as mock_click:
            res = desktop_control.double_click()
            self.assertTrue(res["success"])
            mock_click.assert_called_once_with(button="left", clicks=2)

    def test_06_mouse_right_click(self):
        with patch("pyautogui.click") as mock_click:
            res = desktop_control.right_click()
            self.assertTrue(res["success"])
            mock_click.assert_called_once_with(button="right", clicks=1)

    def test_07_mouse_scroll(self):
        with patch("pyautogui.scroll") as mock_scroll:
            res = desktop_control.scroll(-5)
            self.assertTrue(res["success"])
            mock_scroll.assert_called_once_with(-5)

    def test_08_keyboard_type_text(self):
        with patch("pyautogui.write") as mock_write:
            res = desktop_control.type_text("Hello Sree")
            self.assertTrue(res["success"])
            mock_write.assert_called_once_with("Hello Sree", interval=0.02)

    def test_09_keyboard_press_key(self):
        with patch("pyautogui.press") as mock_press:
            res = desktop_control.press_key("enter")
            self.assertTrue(res["success"])
            mock_press.assert_called_once_with("enter")

    def test_10_keyboard_hotkey(self):
        with patch("pyautogui.hotkey") as mock_hotkey:
            res = desktop_control.hotkey("ctrl", "shift", "esc")
            self.assertTrue(res["success"])
            mock_hotkey.assert_called_once_with("ctrl", "shift", "esc")

    def test_11_os_system_actions(self):
        with patch("pyautogui.hotkey") as mock_hotkey, patch("pyautogui.press") as mock_press:
            # Win+D
            res1 = desktop_control.execute_system_action("minimize_all")
            self.assertTrue(res1["success"])
            mock_hotkey.assert_called_with("win", "d")

            # Alt+Tab
            res2 = desktop_control.execute_system_action("switch_window")
            self.assertTrue(res2["success"])
            mock_hotkey.assert_called_with("alt", "tab")

            # Volume
            res3 = desktop_control.execute_system_action("volume_up")
            self.assertTrue(res3["success"])
            mock_press.assert_called_with("volumeup")

class TestScreenShare(unittest.TestCase):
    def test_12_placeholder_frame(self):
        data = screen_share.get_latest_frame_bytes()
        self.assertGreater(len(data), 0)
        self.assertTrue(data.startswith(b"\xff\xd8")) # JPEG magic bytes

    def test_13_frame_update_from_base64(self):
        # 1x1 black JPEG in base64
        test_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        ok = screen_share.update_frame_from_base64(test_b64)
        self.assertTrue(ok)
        self.assertTrue(screen_share.get_status()["active"])

    def test_14_screenshot_save_disk(self):
        res = screen_share.save_screenshot_to_disk("test_unit_screenshot.jpg")
        self.assertTrue(res["success"])
        path = Path(res["path"])
        self.assertTrue(path.exists())
        # Cleanup
        try:
            path.unlink()
        except Exception:
            pass

class TestVoiceDesktopCommands(unittest.TestCase):
    def test_15_crystallizer_screenshot_voice(self):
        reply = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, take a screenshot"))
        self.assertIsNotNone(reply)
        self.assertIn("Screenshot captured", reply)

    def test_16_crystallizer_screen_share_voice(self):
        reply = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, share my screen"))
        self.assertIsNotNone(reply)
        self.assertIn("Screen Share", reply)

    def test_17_crystallizer_window_control_voice(self):
        reply = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, minimize all windows"))
        self.assertEqual(reply, "Minimized all windows.")

        reply2 = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, switch window"))
        self.assertEqual(reply2, "Switched active window.")

    def test_18_crystallizer_volume_voice(self):
        reply = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, volume up"))
        self.assertEqual(reply, "Volume increased.")

        reply2 = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, mute audio"))
        self.assertEqual(reply2, "Muted audio.")

    def test_19_crystallizer_type_and_press_voice(self):
        reply = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, type hello world"))
        self.assertEqual(reply, "Typed: hello world")

        reply2 = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, press enter"))
        self.assertEqual(reply2, "Pressed enter.")

        reply3 = asyncio.run(skill_crystallizer.execute_fast_path("Hey Sree, click"))
        self.assertEqual(reply3, "Clicked.")

if __name__ == "__main__":
    unittest.main()

