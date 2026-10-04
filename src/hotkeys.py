"""Global hotkeys for CYPHERpc."""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

try:
    import keyboard
except ImportError:
    keyboard = None  # type: ignore


class HotkeyManager:
    """
    Default bindings:
      F8  – AI toggle
      F9  – Overlay toggle
      F10 – Voice hints toggle
      F11 – Push-to-talk
      Ctrl+Shift+C – Control Center
      Ctrl+Shift+Esc – Emergency stop (also OS reserved; may need alternative)
      Ctrl+Shift+P – Command palette
    """

    def __init__(self) -> None:
        self._bound: list[str] = []
        self.enabled = True

    def bind(self, key: str, callback: Callable[[], None]) -> None:
        if keyboard is None:
            logger.warning("keyboard package not installed – hotkeys disabled")
            return
        try:
            keyboard.add_hotkey(key, callback)
            self._bound.append(key)
            logger.info("Hotkey bound: %s", key)
        except Exception as e:
            logger.warning("Failed to bind %s: %s", key, e)

    def unbind_all(self) -> None:
        if keyboard is None:
            return
        for key in self._bound:
            try:
                keyboard.remove_hotkey(key)
            except Exception:
                pass
        self._bound.clear()

    def register_defaults(
        self,
        on_ai_toggle: Callable[[], None] | None = None,
        on_overlay: Callable[[], None] | None = None,
        on_voice: Callable[[], None] | None = None,
        on_ptt: Callable[[], None] | None = None,
        on_cc: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_palette: Callable[[], None] | None = None,
    ) -> None:
        if on_ai_toggle:
            self.bind("F8", on_ai_toggle)
        if on_overlay:
            self.bind("F9", on_overlay)
        if on_voice:
            self.bind("F10", on_voice)
        if on_ptt:
            self.bind("F11", on_ptt)
        if on_cc:
            self.bind("ctrl+shift+c", on_cc)
        if on_stop:
            self.bind("ctrl+shift+x", on_stop)  # Esc often reserved
        if on_palette:
            self.bind("ctrl+shift+p", on_palette)
