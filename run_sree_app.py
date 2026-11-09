"""
SREE Standalone Application & Software Controller for Windows
Entrypoint for running SREE as a native Windows software application.
Features:
- In-process high performance FastAPI backend engine
- Native Windows System Tray (pystray) with Arc Reactor icon
- Full System Tray Control Menu (Voice toggle, Biometrics toggle, Startup toggle, Screen share)
- Auto-starts Ollama daemon
- Auto-starts silent background voice listener ("Hey Sree")
- Dedicated frameless SREE Holographic Cockpit window
- One-click installer & shortcut creator
"""

import sys
import os

# Redirect stdout/stderr if running in windowed mode (console=False)
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

import time
import json
import socket
import threading
import subprocess
import urllib.request
import webbrowser
from pathlib import Path
import multiprocessing

# Freeze support for Windows PyInstaller
multiprocessing.freeze_support()

import pystray
from pystray import MenuItem as item, Menu
from PIL import Image, ImageDraw

from backend.app.core.config import settings

PORT = settings.PORT
URL = f"http://127.0.0.1:{PORT}"

_current_app_process = None
_tray_icon = None

def get_resource_path(relative_path: str) -> Path:
    """Resolves resource paths in development and PyInstaller bundled environments."""
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidate = base_dir / relative_path
        if candidate.exists():
            return candidate
        # Check adjacent to executable
        exe_candidate = Path(sys.executable).parent / relative_path
        if exe_candidate.exists():
            return exe_candidate
        # Check APPDATA
        appdata_candidate = Path(os.environ.get("APPDATA", str(Path.home()))) / "SREE" / relative_path
        if appdata_candidate.exists():
            return appdata_candidate

    root_dir = Path(__file__).resolve().parent
    return root_dir / relative_path

def ensure_appdata_scripts() -> Path:
    """Ensures background_listener.ps1 is persisted in %APPDATA%/SREE/scripts."""
    appdata_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "SREE" / "scripts"
    appdata_dir.mkdir(parents=True, exist_ok=True)
    target_ps = appdata_dir / "background_listener.ps1"

    source_ps = get_resource_path("scripts/background_listener.ps1")
    if source_ps and source_ps.exists():
        try:
            import shutil
            shutil.copy2(source_ps, target_ps)
        except Exception:
            pass

    return target_ps if target_ps.exists() else source_ps

# ==============================================================================
# Service Checks & Lifecycle
# ==============================================================================

def is_service_ready(url: str) -> bool:
    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=1.2) as res:
            return res.status == 200
    except Exception:
        return False

def is_ollama_running() -> bool:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.2) as res:
            return res.status == 200
    except Exception:
        return False

def ensure_ollama():
    """Checks and starts local Ollama daemon if present."""
    if not is_ollama_running():
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            time.sleep(1.5)
        except Exception:
            pass

def start_backend_in_thread():
    """Starts FastAPI uvicorn server in a daemon thread inside this process."""
    if is_service_ready(URL):
        return

    try:
        import uvicorn
        from backend.app.main import app

        config = uvicorn.Config(app=app, host="0.0.0.0", port=PORT, log_level="warning")
        server = uvicorn.Server(config)

        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # Wait up to 10 seconds for backend
        for _ in range(20):
            if is_service_ready(URL):
                return
            time.sleep(0.5)
    except Exception as e:
        pass

# ==============================================================================
# Background Voice Listener Management
# ==============================================================================

def is_listener_running() -> bool:
    """Checks if background_listener.ps1 is actively running."""
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = ' '.join(p.info['cmdline'] or []).lower()
                if 'background_listener' in cmd and 'powershell' in p.info['name'].lower():
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def stop_background_listener():
    """Terminates any running background listener processes."""
    try:
        import psutil
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = ' '.join(p.info['cmdline'] or []).lower()
                if 'background_listener' in cmd and 'powershell' in p.info['name'].lower():
                    p.kill()
            except Exception:
                pass
    except Exception:
        pass

def start_background_listener():
    """Starts background_listener.ps1 in a hidden window."""
    if is_listener_running():
        return

    ps_script = ensure_appdata_scripts()
    if ps_script and ps_script.exists():
        try:
            subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(ps_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except Exception:
            pass

def toggle_background_listener(icon=None, item=None):
    """Toggles the background listener on or off."""
    if is_listener_running():
        stop_background_listener()
    else:
        start_background_listener()
    if icon:
        icon.update_menu()

# ==============================================================================
# Windows Startup & Shortcuts
# ==============================================================================

def get_startup_folder() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        p = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if p.exists():
            return p
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def is_startup_enabled() -> bool:
    s_folder = get_startup_folder()
    return (s_folder / "SREE_Background_Assistant.vbs").exists() or (s_folder / "SREE.lnk").exists()

def toggle_startup(icon=None, item=None):
    s_folder = get_startup_folder()
    vbs = s_folder / "SREE_Background_Assistant.vbs"
    lnk = s_folder / "SREE.lnk"

    if is_startup_enabled():
        if vbs.exists(): vbs.unlink()
        if lnk.exists(): lnk.unlink()
    else:
        if getattr(sys, "frozen", False):
            target = sys.executable
            ps_script = f"""
            $WshShell = New-Object -comObject WScript.Shell
            $s = $WshShell.CreateShortcut('{lnk}')
            $s.TargetPath = '{target}'
            $s.WorkingDirectory = '{Path(target).parent}'
            $s.Description = 'SREE AI Assistant'
            $s.Save()
            """
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            ps_script = ensure_appdata_scripts()
            content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{ps_script}""", 0, False\n'
            with open(vbs, "w", encoding="utf-8") as f:
                f.write(content)

    if icon:
        icon.update_menu()

def get_desktop_dir() -> Path:
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
            text=True
        ).strip()
        if out and Path(out).exists():
            return Path(out)
    except Exception:
        pass
    userprofile = Path(os.environ.get("USERPROFILE", str(Path.home())))
    if (userprofile / "OneDrive" / "Desktop").exists():
        return userprofile / "OneDrive" / "Desktop"
    return userprofile / "Desktop"

def create_desktop_and_start_menu_shortcuts():
    """Installs Desktop and Start Menu shortcuts for SREE."""
    try:
        exe_path = sys.executable if getattr(sys, "frozen", False) else str(Path(__file__).resolve().parent / "dist" / "SREE.exe")
        icon_path = str(get_resource_path("sree.ico"))
        work_dir = str(Path(exe_path).parent)

        # 1. Desktop
        desktop_dir = get_desktop_dir()
        desktop_lnk = desktop_dir / "SREE AI Assistant.lnk"

        # 2. Start Menu
        start_menu_dir = Path(os.environ.get("APPDATA", str(Path.home()))) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "SREE"
        start_menu_dir.mkdir(parents=True, exist_ok=True)
        start_menu_lnk = start_menu_dir / "SREE AI Assistant.lnk"

        ps_script = f"""
        $WshShell = New-Object -comObject WScript.Shell

        # Desktop
        $d = $WshShell.CreateShortcut('{desktop_lnk}')
        $d.TargetPath = '{exe_path}'
        $d.WorkingDirectory = '{work_dir}'
        if (Test-Path '{icon_path}') {{ $d.IconLocation = '{icon_path}, 0' }}
        $d.Description = 'SREE - Personal AI Assistant & Desktop Controller'
        $d.Save()

        # Start Menu
        $s = $WshShell.CreateShortcut('{start_menu_lnk}')
        $s.TargetPath = '{exe_path}'
        $s.WorkingDirectory = '{work_dir}'
        if (Test-Path '{icon_path}') {{ $s.IconLocation = '{icon_path}, 0' }}
        $s.Description = 'SREE - Personal AI Assistant & Desktop Controller'
        $s.Save()
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

# ==============================================================================
# Voice Verification Setting
# ==============================================================================

def is_voice_verified() -> bool:
    try:
        req = urllib.request.Request(f"{URL}/api/voice/status")
        with urllib.request.urlopen(req, timeout=1.2) as res:
            data = json.loads(res.read().decode())
            return data.get("enabled", False)
    except Exception:
        return False

def toggle_voice_verification(icon=None, item=None):
    try:
        curr = is_voice_verified()
        body = json.dumps({"enabled": not curr}).encode()
        req = urllib.request.Request(f"{URL}/api/voice/toggle", data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=2.0)
    except Exception:
        pass
    if icon:
        icon.update_menu()

# ==============================================================================
# Window & UI Launching
# ==============================================================================

def launch_app_window(icon=None, item=None):
    """Opens dedicated standalone app window using Microsoft Edge or Google Chrome."""
    global _current_app_process

    browser_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ]

    for exe in browser_paths:
        if os.path.exists(exe):
            _current_app_process = subprocess.Popen([
                exe,
                f"--app={URL}",
                "--window-size=1280,840"
            ])
            return _current_app_process

    # Fallback to default browser
    webbrowser.open(URL)
    return None

def open_screen_share(icon=None, item=None):
    """Opens the live screen share viewer in the default browser."""
    webbrowser.open(f"{URL}#screenModal")

def open_in_browser(icon=None, item=None):
    webbrowser.open(URL)

# ==============================================================================
# System Tray Icon & Menu
# ==============================================================================

def get_tray_image():
    ico_path = get_resource_path("sree.ico")
    if ico_path and ico_path.exists():
        try:
            return Image.open(str(ico_path))
        except Exception:
            pass

    # Draw glowing cyan Arc Reactor icon in PIL
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], outline=(0, 242, 254, 255), width=3)
    draw.ellipse([16, 16, 48, 48], outline=(0, 255, 179, 255), width=2)
    draw.ellipse([24, 24, 40, 40], fill=(0, 255, 179, 255))
    return img

def restart_services(icon=None, item=None):
    """Restarts listener and ensures backend."""
    stop_background_listener()
    time.sleep(0.5)
    start_background_listener()
    if icon:
        icon.update_menu()

def exit_sree(icon=None, item=None):
    """Cleanly terminates all SREE components and exits."""
    global _tray_icon
    stop_background_listener()
    if _tray_icon:
        _tray_icon.stop()
    os._exit(0)

def build_tray_menu():
    return Menu(
        item('⚡ Open SREE Cockpit', launch_app_window, default=True),
        Menu.SEPARATOR,
        item('🎙️ Voice Wake-Word ("Hey Sree")', toggle_background_listener, checked=lambda item: is_listener_running()),
        item('🔒 Speaker Biometric Gate', toggle_voice_verification, checked=lambda item: is_voice_verified()),
        item('🖥️ Live Screen Share', open_screen_share),
        item('🚀 Start with Windows', toggle_startup, checked=lambda item: is_startup_enabled()),
        Menu.SEPARATOR,
        item('🌐 Open in Browser', open_in_browser),
        item('🔄 Restart Voice Listener', restart_services),
        Menu.SEPARATOR,
        item('❌ Exit SREE', exit_sree)
    )

# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    global _tray_icon

    # If --install passed, configure shortcuts and startup
    if "--install" in sys.argv:
        create_desktop_and_start_menu_shortcuts()
        toggle_startup()

    # 1. Start Ollama and Backend Server
    ensure_ollama()
    start_backend_in_thread()

    # 2. Start Silent Background Voice Listener
    start_background_listener()

    # 3. Create Shortcuts on first run if not existing
    create_desktop_and_start_menu_shortcuts()

    # 4. Open SREE Cockpit Window
    launch_app_window()

    # 5. Initialize System Tray Icon (runs message loop on main thread)
    tray_image = get_tray_image()
    _tray_icon = pystray.Icon(
        "SREE",
        tray_image,
        "SREE – Personal AI Assistant",
        build_tray_menu()
    )

    try:
        _tray_icon.run()
    except KeyboardInterrupt:
        exit_sree()

if __name__ == "__main__":
    main()
