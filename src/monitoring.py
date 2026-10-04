"""PC monitoring dashboard data."""

from __future__ import annotations

from typing import Any

from src.performance import PerformanceManager
from src.agent import Agent
from src.overlay import Overlay
from src.voice import VoiceService
from src.settings import Settings


class MonitoringDashboard:
    def __init__(
        self,
        settings: Settings,
        agent: Agent,
        overlay: Overlay,
        voice: VoiceService,
        performance: PerformanceManager,
        active_game: str | None = None,
    ):
        self.settings = settings
        self.agent = agent
        self.overlay = overlay
        self.voice = voice
        self.performance = performance
        self.active_game = active_game

    def snapshot(self) -> dict[str, Any]:
        stats = self.performance.get_stats()
        agent_status = self.agent.status()
        return {
            **stats,
            "active_game": self.active_game,
            "ai": agent_status,
            "overlay": self.overlay.snapshot(),
            "voice_enabled": self.voice.enabled,
            "voice_hints": self.voice.hints_enabled,
            "selected_monitor": self.settings.selected_monitor,
            "privacy_mode": self.settings.privacy_mode,
        }
