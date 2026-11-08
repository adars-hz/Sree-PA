"""
Security Allowlist for Controlled Laptop Automation
Restricts execution strictly to pre-authorized applications and approved directories.
"""

import os
from pathlib import Path
from typing import Dict, Any, List

# Allowlisted applications on Windows with their safe executable commands
ALLOWLISTED_APPLICATIONS: Dict[str, Dict[str, Any]] = {
    "notepad": {
        "name": "Notepad",
        "command": ["notepad.exe"],
        "description": "Windows standard text editor"
    },
    "calculator": {
        "name": "Calculator",
        "command": ["calc.exe"],
        "description": "Windows system calculator"
    },
    "explorer": {
        "name": "File Explorer",
        "command": ["explorer.exe"],
        "description": "Windows file manager"
    },
    "browser": {
        "name": "Default Browser",
        "command": ["cmd", "/c", "start", "https://google.com"],
        "description": "System default web browser"
    },
    "terminal": {
        "name": "Command Terminal",
        "command": ["cmd.exe", "/c", "start", "cmd.exe"],
        "description": "Windows command prompt"
    },
    "taskmgr": {
        "name": "Task Manager",
        "command": ["taskmgr.exe"],
        "description": "Windows system task manager"
    },
    "vscode": {
        "name": "Visual Studio Code",
        "command": ["code"],
        "description": "Code editor"
    }
}

# Approved directories where file searches and reads are permitted
def get_approved_directories() -> List[Path]:
    user_home = Path.home()
    approved = [
        user_home / "Documents",
        user_home / "Downloads",
        user_home / "Desktop",
        Path("D:/sri")
    ]
    return [p for p in approved if p.exists()]

