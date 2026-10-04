"""Safe process priority management (Normal / High only)."""

from __future__ import annotations

import logging
from typing import Literal

import psutil

logger = logging.getLogger(__name__)

PriorityLevel = Literal["normal", "high"]

# Never use REALTIME
_PRIORITY_MAP = {
    "normal": psutil.NORMAL_PRIORITY_CLASS if hasattr(psutil, "NORMAL_PRIORITY_CLASS") else None,
    "high": psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, "HIGH_PRIORITY_CLASS") else None,
}


def set_process_priority(pid: int, level: PriorityLevel) -> bool:
    """Set priority of a process. Returns True on success."""
    if level not in ("normal", "high"):
        logger.warning("Invalid priority level: %s", level)
        return False
    try:
        p = psutil.Process(pid)
        value = _PRIORITY_MAP.get(level)
        if value is None:
            # Non-Windows fallback
            nice = 0 if level == "normal" else -5
            p.nice(nice)
        else:
            p.nice(value)
        logger.info("Set priority of PID %s to %s", pid, level)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.warning("Cannot set priority for PID %s: %s", pid, e)
        return False


def find_pids_by_name(name: str) -> list[int]:
    name_l = name.lower()
    pids = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == name_l:
                pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids
