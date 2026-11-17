# Pull Request: Multi-Monitor Desktop Control & Screen Coordinate Normalization

**Target Repository**: `adars-hz/Sree-PA`  
**Base Branch**: `main`  
**Head Branch**: `PRN-6:feature/multi-monitor-desktop-control`  
**Closes**: #5  
**Author**: PRN-6  

---

## 📌 Title
```
feat: multi-monitor enumeration, coordinate normalization & display selector (closes #5)
```

---

## 📖 Description & Summary

This pull request resolves **GitHub Issue #5**: *Multi-Monitor Desktop Control & Screen Coordinate Normalization*.

Previously, PyAutoGUI actions were restricted to the primary screen dimensions (`self.screen_width`), which clamped cursor movement to display 1 and made it impossible to control apps on secondary or tertiary monitors. Furthermore, fixed pixel coordinates failed across displays with varying DPI scaling or when interacting via the remote PWA screen viewer.

---

## 🛠️ Key Changes & Problem Resolutions

### 1. 🖥️ Native Monitor Enumeration (`backend/app/automation/desktop_control.py`)
- Implemented native display enumeration via Win32 `EnumDisplayMonitors` using Python's standard `ctypes` library (zero extra external dependencies).
- Detects each display's device name, resolution, `(left, top, right, bottom)` bounding box coordinates, and primary monitor status.
- Added graceful cross-platform fallback for headless or non-Windows environments.

### 2. 📐 Virtual Multi-Monitor Geometry & Active Monitor Selection
- Added `get_virtual_screen_geometry()` to calculate the global multi-monitor bounding box spanning all connected displays.
- Added `set_active_monitor(monitor_index)` and `get_active_monitor()` to dynamically select the target display for screen viewing and automation.

### 3. 🎯 DPI-Aware Coordinate Normalization
- Added `normalize_coordinates(x, y, x_ratio, y_ratio, monitor_index)`:
  - **Ratio-Based Normalization**: Normalizes relative ratios `(0.0 to 1.0)` to target display coordinates, allowing responsive touchscreen and web UI clicks to map with 100% precision regardless of DPI scaling or client viewport zoom.
  - **Monitor Offsets**: Offsets relative `(x, y)` pixels by target monitor `(left, top)` coordinates.
  - **Virtual Boundary Clamping**: Prevents cursor clamping to monitor 1 by clamping across the complete virtual multi-monitor desktop.
- Updated `move_mouse`, `click`, `double_click`, `right_click`, and `drag_to` to accept `x_ratio`, `y_ratio`, `monitor_index`, and `normalized`.

### 4. 🌐 REST API Endpoints (`backend/app/api/desktop.py`)
- `GET /api/desktop/monitors`: Returns all connected monitors, active display, and virtual screen geometry.
- `POST /api/desktop/monitors/select`: Switches active display monitor.
- Updated `GET /api/desktop/status` to include monitor telemetry.
- Updated `POST /api/desktop/mouse` with `x_ratio`, `y_ratio`, `monitor_index`, and `normalized` flags.

### 5. 🎨 Frontend HUD Display Selector & Normalized Click Dispatch (`frontend/`)
- Added a Monitor selector dropdown (`#desktopMonitorSelect`) in the desktop viewer toolbar.
- Populates connected monitors dynamically upon opening the screen viewer modal.
- Clicking or tapping on the live screen feed computes normalized `x_ratio` and `y_ratio` and dispatches clicks to the active monitor.

---

## 🧪 Verification & Test Results

Added 6 new unit tests to `tests/test_desktop_screen_suite.py` (`TestMultiMonitorControl`):
- `test_20_monitor_enumeration`: Verifies enumeration of monitors with valid resolutions and attributes.
- `test_21_virtual_screen_geometry`: Validates virtual multi-monitor bounding box calculations.
- `test_22_active_monitor_selection`: Tests active monitor switching and invalid index handling.
- `test_23_coordinate_normalization_ratios`: Validates ratio mapping (50%, 50% maps to monitor center).
- `test_24_coordinate_normalization_clamping`: Validates edge clamping for out-of-bounds coordinates.
- `test_25_multi_monitor_mouse_dispatch`: Validates click dispatching with ratio coordinates.

```bash
$ python tests/test_desktop_screen_suite.py
.........................
----------------------------------------------------------------------
Ran 25 tests in 0.51s
OK

$ python tests/test_unit_suite.py
----------------------------------------------------------------------
Ran 90 tests in 9.38s
OK (STATUS: 100% PASS RATE)
```
**Total: 115 passing automated tests.**

---

## 📋 Checklist
- [x] Closes Issue #5.
- [x] Adheres to project coding standards and architecture rules.
- [x] Zero extra external dependencies added (uses standard `ctypes`).
- [x] All 115 unit and automation tests passing (100% pass rate).
- [x] Safe fallbacks implemented for non-Windows/headless environments.
