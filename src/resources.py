"""Resource path helpers (works in dev + PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str | Path) -> Path:
    """
    Resolve a resource file path for both:
    - dev/source runs (relative to repo root)
    - PyInstaller builds (relative to sys._MEIPASS / extracted bundle)
    """
    rel = Path(relative_path)

    # PyInstaller onefile/onedir
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel

    # Repo root (main.py is at root; src/ is one level down)
    return Path(__file__).resolve().parent.parent / rel

