"""
SREE Native Desktop Application Launcher (Windows)
Runs SREE as a dedicated desktop application with native window controls,
auto-launching Ollama and the FastAPI backend.
"""

import sys
import os
import time
import socket
import subprocess
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

PORT = 8005
URL = f"http://127.0.0.1:{PORT}"

def is_service_ready(url: str) -> bool:
    """Check if the given HTTP service responds."""
    try:
        req = urllib.request.Request(f"{url}/health")
        with urllib.request.urlopen(req, timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False

def is_ollama_running() -> bool:
    """Check if Ollama is running on 11434."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False

def ensure_services():
    """Start Ollama and FastAPI backend if not already active."""
    # 1. Ollama
    if not is_ollama_running():
        print("[*] Launching Ollama daemon in background...")
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
        )
        time.sleep(2)

    # 2. SREE Backend
    if not is_service_ready(URL):
        print("[*] Launching SREE FastAPI backend on port 8005...")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", str(PORT)],
            cwd=str(ROOT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
        )
        
        # Wait until backend responds
        for _ in range(20):
            if is_service_ready(URL):
                break
            time.sleep(0.5)

def launch_standalone_app_window():
    """Launch via Google Chrome or Microsoft Edge dedicated app mode for full Web Speech recognition."""
    browser_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ]
    
    for exe in browser_paths:
        if os.path.exists(exe):
            print(f"[*] Launching SREE Dedicated App Window via {Path(exe).name}...")
            subprocess.Popen([
                exe,
                f"--app={URL}",
                "--window-size=1280,840",
                "--app-auto-launched"
            ])
            return True
            
    # Fallback to pywebview if available
    try:
        import webview
        print("[*] Launching pywebview window...")
        window = webview.create_window(
            title="SREE – Personal AI Assistant",
            url=URL,
            width=1280,
            height=840,
            min_size=(450, 650),
            resizable=True,
            background_color="#030712"
        )
        webview.start(debug=False)
        return True
    except Exception:
        pass

    # Generic browser open
    import webbrowser
    webbrowser.open(URL)
    return True

def main():
    print("=" * 60)
    print("      LAUNCHING SREE DESKTOP APPLICATION")
    print("=" * 60)
    
    ensure_services()
    launch_standalone_app_window()

if __name__ == "__main__":
    main()

