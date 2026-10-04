"""Background monitor that applies game priority when process starts."""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable

from src.game_profiles import GAME_PROFILES, find_profile_by_process
from src.priority import find_pids_by_name, set_process_priority

logger = logging.getLogger(__name__)


class PriorityMonitor:
    """Watches for game processes and applies configured priority once."""

    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._applied: set[int] = set()  # PIDs we already set
        self.on_game_detected: Callable[[str, int], None] | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="PriorityMonitor")
        self._thread.start()
        logger.info("PriorityMonitor started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("PriorityMonitor stopped")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._scan()
            except Exception:
                logger.exception("PriorityMonitor scan error")
            self._stop.wait(self.interval)

    def _scan(self) -> None:
        for profile in GAME_PROFILES.values():
            for proc_name in profile.process_names:
                for pid in find_pids_by_name(proc_name):
                    if pid in self._applied:
                        continue
                    level = profile.process_priority  # type: ignore
                    if set_process_priority(pid, level):  # type: ignore
                        self._applied.add(pid)
                        logger.info(
                            "Applied %s priority to %s (PID %s)",
                            level, profile.display_name, pid,
                        )
                        if self.on_game_detected:
                            self.on_game_detected(profile.name, pid)

        # Cleanup dead PIDs
        alive = set()
        import psutil
        for pid in list(self._applied):
            if psutil.pid_exists(pid):
                alive.add(pid)
        self._applied = alive
