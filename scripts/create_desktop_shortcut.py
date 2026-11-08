"""
Creates a Windows Desktop Shortcut for SREE Personal AI Assistant
Dynamically resolves Desktop path (handling OneDrive redirects).
"""

import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
VBS_PATH = ROOT_DIR / "Launch_SREE.vbs"
BAT_PATH = ROOT_DIR / "Launch_SREE.bat"

def get_desktop_dir() -> Path:
    cmd = "[Environment]::GetFolderPath('Desktop')"
    try:
        out = subprocess.check_output(["powershell", "-NoProfile", "-Command", cmd]).decode().strip()
        if out and Path(out).exists():
            return Path(out)
    except Exception:
        pass
    return Path.home() / "Desktop"

def create_shortcut():
    desktop_dir = get_desktop_dir()
    shortcut_path = desktop_dir / "SREE Personal AI.lnk"

    ps_script = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = 'wscript.exe'
    $Shortcut.Arguments = '"{VBS_PATH}"'
    $Shortcut.WorkingDirectory = '{ROOT_DIR}'
    $Shortcut.Description = 'SREE - Personal AI Assistant (Zero Console)'
    $Shortcut.IconLocation = 'shell32.dll, 14'
    $Shortcut.Save()
    """

    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], check=True)
        print(f"[+] Successfully created Windows Desktop Shortcut at:\n    {shortcut_path}")
    except Exception as e:
        print(f"[!] Failed to create shortcut: {e}")

if __name__ == "__main__":
    create_shortcut()
