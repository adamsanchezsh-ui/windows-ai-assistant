"""Privacy Center + Emergency Stop."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class PrivacyState:
    microphone: bool = False
    screen: bool = False
    files: bool = True
    internet: bool = True
    active_tools: list[str] = field(default_factory=list)
    privacy_mode: bool = False


class PrivacyCenter:
    """
    Ukazuje, co CYPHERpc právě používá, a umí vše jedním tlačítkem vypnout.
    """

    def __init__(self) -> None:
        self.state = PrivacyState()
        self._stop_callbacks: list[Callable[[], None]] = []

    def register_stop_callback(self, cb: Callable[[], None]) -> None:
        self._stop_callbacks.append(cb)

    def update(
        self,
        microphone: bool | None = None,
        screen: bool | None = None,
        files: bool | None = None,
        internet: bool | None = None,
        active_tools: list[str] | None = None,
    ) -> None:
        if microphone is not None:
            self.state.microphone = microphone
        if screen is not None:
            self.state.screen = screen
        if files is not None:
            self.state.files = files
        if internet is not None:
            self.state.internet = internet
        if active_tools is not None:
            self.state.active_tools = active_tools

    def snapshot(self) -> dict[str, Any]:
        return {
            "privacy_mode": self.state.privacy_mode,
            "microphone": self.state.microphone,
            "screen": self.state.screen,
            "files": self.state.files,
            "internet": self.state.internet,
            "active_tools": list(self.state.active_tools),
        }

    def enable_privacy_mode(self) -> dict[str, Any]:
        """One-click: stop vision, mic, wake word, automation."""
        self.state.privacy_mode = True
        self.state.microphone = False
        self.state.screen = False
        for cb in self._stop_callbacks:
            try:
                cb()
            except Exception:
                logger.exception("Privacy stop callback failed")
        logger.warning("PRIVACY MODE ENABLED")
        return self.snapshot()

    def disable_privacy_mode(self) -> dict[str, Any]:
        self.state.privacy_mode = False
        logger.info("Privacy mode disabled")
        return self.snapshot()

    def emergency_stop(self) -> dict[str, Any]:
        """Okamžitě zastaví veškerou automatizaci."""
        result = self.enable_privacy_mode()
        result["emergency_stop"] = True
        logger.critical("EMERGENCY STOP")
        return result
