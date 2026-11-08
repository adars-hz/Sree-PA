"""
SREE Master Startup Script
Discovers LAN IP for Android phone access, verifies Ollama, and starts the FastAPI backend.
"""

import os
import sys
import socket
import subprocess
import time
import urllib.request
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

def get_local_ip() -> str:
    """Detect LAN IP address to provide the exact URL for Android mobile connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to actually reach external internet; used to determine local interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_ollama_running(url: str = "http://127.0.0.1:11434") -> bool:
    """Verify whether Ollama daemon is reachable."""
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def list_installed_models(url: str = "http://127.0.0.1:11434") -> list:
    """Retrieve list of currently downloaded models."""
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            return [m.get("name") for m in data.get("models", [])]
    except Exception:
        return []

def main():
    print("=" * 65)
    print("      SREE - PERSONAL AI ASSISTANT (PROJECT LAUNCHER)")
    print("          'Your Personal AI. Your Digital World.'")
    print("=" * 65)
    
    from backend.app.core.config import settings
    local_ip = get_local_ip()
    port = settings.PORT

    print(f"\n[1/3] Checking Ollama Engine...")
    if not is_ollama_running():
        print("  [!] Ollama is not running on 127.0.0.1:11434.")
        print("  [*] Attempting to launch Ollama background process...")
        try:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
        except Exception as e:
            print(f"  [X] Failed to auto-launch Ollama: {e}")
            print("  [!] Please run 'ollama serve' in another terminal window.")
    
    if is_ollama_running():
        models = list_installed_models()
        print(f"  [+] Ollama is ACTIVE! (Port 11434)")
        print(f"  [+] Installed Models: {', '.join(models) if models else 'None yet'}")
    else:
        print("  [!] Warning: Ollama could not be contacted. Starting backend anyway...")

    print(f"\n[2/3] Preparing Network Endpoints...")
    print(f"  --> Laptop Browser URL : http://localhost:{port}")
    print(f"  --> Android Phone URL  : http://{local_ip}:{port}")

    print(f"\n[3/3] Starting SREE FastAPI Server...")
    print("-" * 65)
    
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)

if __name__ == "__main__":
    main()

