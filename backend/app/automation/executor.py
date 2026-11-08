"""
Safe Execution Controller for SREE Laptop Automation
Enforces allowlists, prevents arbitrary shell code execution, and handles safe file browsing.
"""

import os
import subprocess
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from .allowlist import ALLOWLISTED_APPLICATIONS, get_approved_directories

class AutomationExecutor:
    def get_available_apps(self) -> List[Dict[str, Any]]:
        """Returns the list of allowlisted applications available for launch."""
        return [
            {"id": app_id, "name": meta["name"], "description": meta["description"]}
            for app_id, meta in ALLOWLISTED_APPLICATIONS.items()
        ]

    get_allowlisted_apps = get_available_apps

    def launch_application(self, app_id: str) -> Dict[str, Any]:
        """
        Validates the application against the allowlist and launches it in a detached process.
        """
        app_id_clean = app_id.lower().strip()
        if app_id_clean not in ALLOWLISTED_APPLICATIONS:
            return {
                "success": False,
                "error": f"Application '{app_id}' is not in the security allowlist. Only authorized apps can be launched."
            }

        app_meta = ALLOWLISTED_APPLICATIONS[app_id_clean]
        command = app_meta["command"]

        try:
            # Safe detached process launch on Windows
            subprocess.Popen(
                command,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0
            )
            return {
                "success": True,
                "message": f"Successfully launched {app_meta['name']}.",
                "app": app_meta['name']
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to launch {app_meta['name']}: {str(e)}"
            }

    def get_system_telemetry(self) -> Dict[str, Any]:
        """Collects safe hardware telemetry: battery, CPU, RAM, uptime."""
        # Battery
        battery_info = {}
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_info = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                }
        except Exception:
            pass

        # Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        uptime_hours = round(uptime_seconds / 3600, 1)

        return {
            "uptime_hours": uptime_hours,
            "cpu_percent": psutil.cpu_percent(interval=None),
            "ram_percent": psutil.virtual_memory().percent,
            "battery": battery_info or {"status": "Desktop / No battery"}
        }

    def search_approved_files(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Searches for files matching query strictly within approved user folders.
        """
        if not query or len(query.strip()) < 2:
            return []

        results = []
        approved_dirs = get_approved_directories()
        clean_query = query.lower().strip()

        for base_dir in approved_dirs:
            try:
                for root, _, files in os.walk(base_dir):
                    for file in files:
                        if clean_query in file.lower():
                            full_path = Path(root) / file
                            try:
                                stat = full_path.stat()
                                results.append({
                                    "name": file,
                                    "path": str(full_path),
                                    "size_kb": round(stat.st_size / 1024, 1),
                                    "modified": time.ctime(stat.st_mtime)
                                })
                            except Exception:
                                continue
                            if len(results) >= limit:
                                return results
            except Exception:
                continue

        return results

    def read_approved_text_file(self, file_path_str: str, max_chars: int = 4000) -> Dict[str, Any]:
        """
        Safely reads a text or markdown document if it is inside an approved directory.
        """
        target_path = Path(file_path_str).resolve()
        approved_dirs = [p.resolve() for p in get_approved_directories()]

        # Path traversal and boundary security check
        is_safe = any(
            target_path == app_dir or app_dir in target_path.parents
            for app_dir in approved_dirs
        )

        if not is_safe:
            return {
                "success": False,
                "error": "Access denied. The requested file is outside user-approved directories."
            }

        if not target_path.is_file():
            return {"success": False, "error": "File not found or is a directory."}

        # Check file extension
        safe_extensions = {".txt", ".md", ".json", ".csv", ".log", ".py", ".html", ".css", ".js"}
        if target_path.suffix.lower() not in safe_extensions:
            return {"success": False, "error": f"File type '{target_path.suffix}' cannot be previewed."}

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars)
            return {
                "success": True,
                "file_name": target_path.name,
                "content": content,
                "truncated": target_path.stat().st_size > max_chars
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

automation_executor = AutomationExecutor()

