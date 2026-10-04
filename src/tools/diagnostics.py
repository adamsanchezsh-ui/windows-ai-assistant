"""Diagnostics, crash recovery hints, log viewer helpers."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any

import psutil


def system_info() -> dict[str, Any]:
    return {
        "os": platform.platform(),
        "python": sys.version,
        "cpu_count": psutil.cpu_count(),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_free_gb": round(psutil.disk_usage("/").free / (1024**3), 2),
    }


def read_logs(log_dir: Path, lines: int = 0) -> str:
    """lines=0 means entire last log file (no artificial trim beyond practical size)."""
    log_dir = Path(log_dir)
    files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "(no logs)"
    text = files[0].read_text(encoding="utf-8", errors="replace")
    if lines and lines > 0:
        return "\n".join(text.splitlines()[-lines:])
    return text  # full log


def health_check(providers: list[str], data_dir: Path) -> dict[str, Any]:
    return {
        "system": system_info(),
        "providers_configured": providers,
        "data_dir_exists": data_dir.exists(),
        "data_dir_writable": data_dir.exists() and os_access_write(data_dir),
    }


def os_access_write(path: Path) -> bool:
    try:
        test = path / ".write_test"
        test.write_text("ok")
        test.unlink()
        return True
    except Exception:
        return False
