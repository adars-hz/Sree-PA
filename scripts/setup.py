"""
SREE Automated Environment Setup Script
Verifies system dependencies, Python version, creates directories, and checks Ollama.
"""

import sys
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def check_python():
    print("[1/5] Checking Python Version...")
    v = sys.version_info
    print(f"  --> Python {v.major}.{v.minor}.{v.micro} detected.")
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        print("  [X] Python 3.10+ required. Please upgrade Python.")
        return False
    print("  --> PASS: Python version compatible.")
    return True

def setup_env_file():
    print("\n[2/5] Checking Environment Configuration (.env)...")
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("  --> Created .env from .env.example with default values.")
        else:
            print("  [!] .env.example not found.")
    else:
        print("  --> .env already configured.")

def create_directories():
    print("\n[3/5] Initializing Directory Hierarchy...")
    dirs = [
        ROOT_DIR / "data" / "database",
        ROOT_DIR / "data" / "cache",
        ROOT_DIR / "frontend" / "assets" / "icons",
        ROOT_DIR / "frontend" / "css",
        ROOT_DIR / "frontend" / "js",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("  --> PASS: All project directories ready.")

def install_dependencies():
    print("\n[4/5] Verifying Python Dependencies...")
    req_file = ROOT_DIR / "requirements.txt"
    if req_file.exists():
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        subprocess.check_call(cmd)
        print("  --> PASS: All dependencies satisfied.")
    else:
        print("  [!] requirements.txt not found.")

def check_ollama():
    print("\n[5/5] Checking Ollama Installation...")
    ollama_path = shutil.which("ollama")
    if ollama_path:
        print(f"  --> Ollama binary detected: {ollama_path}")
    else:
        print("  [!] Ollama was not found in PATH.")
        print("      Download it for free from https://ollama.com")

def main():
    print("=" * 60)
    print("      PROJECT SREE - SYSTEM SETUP & VERIFICATION")
    print("=" * 60)
    if not check_python():
        sys.exit(1)
    setup_env_file()
    create_directories()
    install_dependencies()
    check_ollama()
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE! You can now start SREE with:")
    print("  python scripts/start.py")
    print("=" * 60)

if __name__ == "__main__":
    main()

