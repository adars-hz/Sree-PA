"""
Desktop Screen Sharing & Remote Control Test Suite for Project SREE
Validates 0ms screen sharing, screenshot capture, mouse/keyboard automation,
OS system shortcuts, and skill crystallizer voice commands.
"""

import unittest
import asyncio
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to sys.path for direct execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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

class TestMultiMonitorControl(unittest.TestCase):
    def test_20_monitor_enumeration(self):
        monitors = desktop_control.get_monitors()
        self.assertIsInstance(monitors, list)
        self.assertGreater(len(monitors), 0)
        first = monitors[0]
        self.assertIn("index", first)
        self.assertIn("name", first)
        self.assertIn("width", first)
        self.assertIn("height", first)
        self.assertIn("is_primary", first)
        self.assertGreater(first["width"], 0)
        self.assertGreater(first["height"], 0)

    def test_21_virtual_screen_geometry(self):
        geom = desktop_control.get_virtual_screen_geometry()
        self.assertIn("left", geom)
        self.assertIn("top", geom)
        self.assertIn("width", geom)
        self.assertIn("height", geom)
        self.assertGreaterEqual(geom["width"], desktop_control.screen_width)
        self.assertGreaterEqual(geom["height"], desktop_control.screen_height)

    def test_22_active_monitor_selection(self):
        res = desktop_control.set_active_monitor(0)
        self.assertTrue(res["success"])
        self.assertEqual(res["active_monitor_index"], 0)
        active = desktop_control.get_active_monitor()
        self.assertEqual(active["index"], 0)

        # Invalid index test
        bad_res = desktop_control.set_active_monitor(999)
        self.assertFalse(bad_res["success"])

    def test_23_coordinate_normalization_ratios(self):
        mon = desktop_control.get_active_monitor()
        # 50% X and 50% Y should be exactly in the center of the monitor
        norm_x, norm_y = desktop_control.normalize_coordinates(
            x_ratio=0.5, y_ratio=0.5, monitor_index=mon["index"]
        )
        expected_x = int(mon["left"] + (0.5 * mon["width"]))
        expected_y = int(mon["top"] + (0.5 * mon["height"]))
        self.assertEqual(norm_x, expected_x)
        self.assertEqual(norm_y, expected_y)

    def test_24_coordinate_normalization_clamping(self):
        mon = desktop_control.get_active_monitor()
        # Out-of-bounds ratios should clamp to monitor edges
        clamped_x, clamped_y = desktop_control.normalize_coordinates(
            x_ratio=1.5, y_ratio=-0.5, monitor_index=mon["index"]
        )
        self.assertEqual(clamped_x, mon["right"] - 1)
        self.assertEqual(clamped_y, mon["top"])

    def test_25_multi_monitor_mouse_dispatch(self):
        with patch("pyautogui.moveTo") as mock_move, patch("pyautogui.click") as mock_click:
            res = desktop_control.click(x_ratio=0.5, y_ratio=0.5, monitor_index=0, button="left")
            self.assertTrue(res["success"])
            self.assertEqual(res["action"], "left_click")
            mock_click.assert_called_once_with(button="left", clicks=1)

if __name__ == "__main__":
    unittest.main()

