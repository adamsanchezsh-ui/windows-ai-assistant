"""Resolve paths for source run and frozen CYPHERpc.exe (PyInstaller)."""

from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Directory containing the exe or project root."""
    if getattr(sys, "frozen", False):
        # PyInstaller one-file / one-dir
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    """Bundled resources (config, etc.)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return app_root()


def ensure_env_file() -> Path:
    """Prefer .env next to exe; create from example if missing."""
    root = app_root()
    env_path = root / ".env"
    if env_path.exists():
        return env_path
    example = root / ".env.example"
    if not example.exists():
        example = resource_root() / ".env.example"
    if example.exists() and not env_path.exists():
        env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    return env_path
