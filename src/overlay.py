"""Always-on-top overlay for AI tips and status."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Overlay:
    """Simple always-on-top overlay (GUI implementation in ui/)."""

    def __init__(self, monitor: int = 1, opacity: float = 0.85):
        self.enabled = False
        self.monitor = monitor
        self.opacity = opacity
        self.current_tip: str = ""
        self.objective: str = ""
        self.ai_status: str = "OFF"

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        logger.info("Overlay %s", "ON" if self.enabled else "OFF")
        return self.enabled

    def set_monitor(self, monitor: int) -> None:
        self.monitor = max(1, min(4, monitor))

    def update(
        self,
        tip: str | None = None,
        objective: str | None = None,
        status: str | None = None,
    ) -> None:
        if tip is not None:
            self.current_tip = tip
        if objective is not None:
            self.objective = objective
        if status is not None:
            self.ai_status = status

    def snapshot(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "monitor": self.monitor,
            "opacity": self.opacity,
            "tip": self.current_tip,
            "objective": self.objective,
            "status": self.ai_status,
        }
