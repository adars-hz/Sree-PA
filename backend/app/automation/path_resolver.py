"""
Dynamic Windows Path Resolution Engine for Project SREE
Resolves active paths dynamically, accounting for OneDrive folder redirection.
"""

import os
from pathlib import Path
from typing import Dict, Optional

class PathResolver:
    def __init__(self):
        self._cache: Dict[str, Path] = {}
        self.refresh()

    def refresh(self):
        """Resolves system paths considering OneDrive redirection."""
        home = Path.home()
        onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer") or str(home / "OneDrive")
        onedrive_path = Path(onedrive) if onedrive else None

        # 1. Desktop
        desktop = home / "Desktop"
        if onedrive_path and (onedrive_path / "Desktop").exists():
            desktop = onedrive_path / "Desktop"
        elif not desktop.exists() and onedrive_path:
            desktop = onedrive_path / "Desktop"
        self._cache["desktop"] = desktop

        # 2. Documents
        documents = home / "Documents"
        if onedrive_path and (onedrive_path / "Documents").exists():
            documents = onedrive_path / "Documents"
        self._cache["documents"] = documents

        # 3. Downloads
        self._cache["downloads"] = home / "Downloads"

        # 4. Pictures
        pictures = home / "Pictures"
        if onedrive_path and (onedrive_path / "Pictures").exists():
            pictures = onedrive_path / "Pictures"
        self._cache["pictures"] = pictures

        # 5. User Home
        self._cache["home"] = home

    def get_desktop(self) -> Path:
        return self._cache.get("desktop", Path.home() / "Desktop")

    def get_documents(self) -> Path:
        return self._cache.get("documents", Path.home() / "Documents")

    def get_downloads(self) -> Path:
        return self._cache.get("downloads", Path.home() / "Downloads")

    def get_pictures(self) -> Path:
        return self._cache.get("pictures", Path.home() / "Pictures")

    def get_home(self) -> Path:
        return self._cache.get("home", Path.home())

    def resolve_target(self, folder_name: str) -> Optional[Path]:
        """Resolves a target folder alias like 'desktop', 'downloads', 'documents'."""
        key = folder_name.lower().strip()
        return self._cache.get(key)

    def get_project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent

    def resolve_path(self, subpath: str) -> Path:
        """Resolves a subpath against OneDrive or standard home paths."""
        parts = Path(subpath).parts
        if not parts:
            return self.get_home()
        first = parts[0].lower().strip()
        base = self.resolve_target(first)
        if base:
            if len(parts) > 1:
                return base / Path(*parts[1:])
            return base
        return self.get_home() / Path(subpath)

    def get_all_approved_roots(self) -> list[Path]:
        """Returns all safe user directories approved for file operations."""
        return [
            self.get_desktop(),
            self.get_documents(),
            self.get_downloads(),
            self.get_pictures()
        ]

path_resolver = PathResolver()
dynamic_path_resolver = path_resolver
