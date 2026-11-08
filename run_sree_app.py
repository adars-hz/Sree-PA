"""
SREE Standalone Application Launcher for Windows
Entrypoint for compiling SREE into a self-contained .exe executable.
Runs the FastAPI backend in-process, checks Ollama, starts the background voice listener,
and launches the native standalone desktop application window.
"""

import sys
import os
import time
import socket
import threading
import subprocess
import urllib.request
from pathlib import Path
import multiprocessing

# Freeze support for Windows PyInstaller
multiprocessing.freeze_support()

PORT = 8005
URL = f"http://127.0.0.1:{PORT}"

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

def start_backend_in_thread():
    """Starts FastAPI uvicorn server in a daemon thread inside this process."""
    if is_service_ready(URL):
        print(f"[+] SREE backend is already active on port {PORT}.")
        return

    print(f"[*] Starting SREE backend server on port {PORT}...")
    try:
        import uvicorn
        from backend.app.main import app
        
        config = uvicorn.Config(app=app, host="0.0.0.0", port=PORT, log_level="warning")
        server = uvicorn.Server(config)
        
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        
        # Wait up to 10 seconds for backend to become healthy
        for _ in range(20):
            if is_service_ready(URL):
                print(f"[+] SREE backend engine initialized on {URL}")
                return
            time.sleep(0.5)
    except Exception as e:
        print(f"[!] Warning: Failed to start in-process backend: {e}")

def ensure_ollama():
    """Checks and starts local Ollama daemon if present."""
    if not is_ollama_running():
        try:
            print("[*] Launching local Ollama server...")
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            time.sleep(1.5)
        except Exception:
            pass

def ensure_background_listener():
    """Starts the native Windows Speech background listener for 'Hey Sree' wake word."""
    # Locate background_listener.ps1
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS)
        candidates.append(meipass / "scripts" / "background_listener.ps1")
        appdata = Path(os.environ.get("APPDATA", str(Path.home()))) / "SREE" / "scripts" / "background_listener.ps1"
        candidates.append(appdata)
    
    root_dir = Path(__file__).resolve().parent
    candidates.append(root_dir / "scripts" / "background_listener.ps1")
    
    ps_script = None
    for c in candidates:
        if c.exists():
            ps_script = c
            break
            
    if ps_script:
        print(f"[*] Activating silent background voice listener ({ps_script.name})...")
        try:
            subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(ps_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except Exception as e:
            print(f"[!] Notice: Background listener skipped: {e}")

def launch_app_window():
    """Opens dedicated standalone app window using Microsoft Edge or Google Chrome."""
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
            print(f"[*] Opening SREE Application Window via {Path(exe).name}...")
            return subprocess.Popen([
                exe,
                f"--app={URL}",
                "--window-size=1280,840"
            ])
            
    # Generic browser fallback
    import webbrowser
    print("[*] Opening SREE in default browser...")
    webbrowser.open(URL)
    return None

def main():
    print("=" * 60)
    print("        SREE – PERSONAL DIGITAL AI ASSISTANT")
    print("=" * 60)
    
    ensure_ollama()
    start_backend_in_thread()
    ensure_background_listener()
    
    win_proc = launch_app_window()
    
    print("\n[+] SREE is actively running!")
    print(f"    Local Web App: {URL}")
    print("    Background Voice: Listening for 'Hey Sree'")
    print("    Press Ctrl+C in this console or close the app window to exit.")
    print("=" * 60)
    
    try:
        if win_proc:
            win_proc.wait()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[-] Shutting down SREE...")

if __name__ == "__main__":
    main()
