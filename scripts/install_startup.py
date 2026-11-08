"""
SREE Windows Auto-Startup Manager
Installs or removes SREE background voice listener from Windows Startup folder.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
VBS_LAUNCHER = SCRIPTS_DIR / "launch_silent.vbs"

def get_startup_folder() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        startup = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if startup.exists():
            return startup
            
    # Fallback to home path
    fallback = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

def install_startup():
    startup_dir = get_startup_folder()
    startup_vbs = startup_dir / "SREE_Background_Assistant.vbs"
    
    ps_script = SCRIPTS_DIR / "background_listener.ps1"
    
    content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{ps_script}""", 0, False
'''
    with open(startup_vbs, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("=" * 65)
    print("      SREE WINDOWS AUTO-STARTUP CONFIGURED")
    print("=" * 65)
    print(f"[+] Installed startup hook: {startup_vbs}")
    print("[+] SREE will now start automatically in the background when your PC boots.")
    print("[+] When your system powers on, you can say 'Hey Sree' anytime to talk live!")
    print("=" * 65)
    return True

def uninstall_startup():
    startup_dir = get_startup_folder()
    startup_vbs = startup_dir / "SREE_Background_Assistant.vbs"
    if startup_vbs.exists():
        startup_vbs.unlink()
        print(f"[+] Removed SREE from Windows Startup folder: {startup_vbs}")
    else:
        print("[-] SREE is not currently registered in Windows Startup.")

def check_status():
    startup_dir = get_startup_folder()
    startup_vbs = startup_dir / "SREE_Background_Assistant.vbs"
    print(f"[*] Windows Startup Folder: {startup_dir}")
    print(f"[*] SREE Auto-Start Status: {'ENABLED (Active on boot)' if startup_vbs.exists() else 'DISABLED'}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("uninstall", "remove", "disable"):
        uninstall_startup()
    elif len(sys.argv) > 1 and sys.argv[1].lower() in ("status", "check"):
        check_status()
    else:
        install_startup()

