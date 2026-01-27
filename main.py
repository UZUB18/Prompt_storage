#!/usr/bin/env python3
"""Prompt Library - Desktop application for managing prompts."""

import os
import sys


def _load_app():
    """Import the app module with PyInstaller-friendly fallback."""
    try:
        from src.app import run  # type: ignore
        return run
    except ModuleNotFoundError:
        # PyInstaller fallback: load from extracted data folder.
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
        src_path = os.path.join(base_dir, "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        from app import run  # type: ignore
        return run


run = _load_app()

if __name__ == "__main__":
    run()
