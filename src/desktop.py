"""Safe desktop control: keyboard, mouse, windows, apps."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

try:
    import pyautogui
    import pygetwindow as gw
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
except ImportError:
    pyautogui = None  # type: ignore
    gw = None  # type: ignore


class DesktopController:
    """Controls keyboard, mouse and windows with safety in mind."""

    def __init__(self, require_confirmation: bool = True):
        self.require_confirmation = require_confirmation

    def _check(self) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui / pygetwindow not installed")

    async def type_text(self, text: str, interval: float = 0.02) -> dict[str, Any]:
        self._check()
        pyautogui.write(text, interval=interval)
        return {"status": "ok", "action": "type", "length": len(text)}

    async def press_key(self, key: str) -> dict[str, Any]:
        self._check()
        pyautogui.press(key)
        return {"status": "ok", "action": "press", "key": key}

    async def hotkey(self, *keys: str) -> dict[str, Any]:
        self._check()
        pyautogui.hotkey(*keys)
        return {"status": "ok", "action": "hotkey", "keys": keys}

    async def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> dict[str, Any]:
        self._check()
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)
        return {"status": "ok", "action": "click", "x": x, "y": y}

    async def move(self, x: int, y: int, duration: float = 0.2) -> dict[str, Any]:
        self._check()
        pyautogui.moveTo(x, y, duration=duration)
        return {"status": "ok", "action": "move", "x": x, "y": y}

    async def list_windows(self) -> list[dict[str, Any]]:
        self._check()
        windows = []
        for w in gw.getAllWindows():
            if w.title.strip():
                windows.append({
                    "title": w.title,
                    "left": w.left,
                    "top": w.top,
                    "width": w.width,
                    "height": w.height,
                    "is_active": w.isActive,
                })
        return windows

    async def focus_window(self, title_substring: str) -> dict[str, Any]:
        self._check()
        matches = [w for w in gw.getAllWindows() if title_substring.lower() in w.title.lower()]
        if not matches:
            return {"status": "error", "message": f"No window matching '{title_substring}'"}
        w = matches[0]
        try:
            w.activate()
        except Exception as e:
            logger.warning("activate failed: %s", e)
            w.minimize()
            w.restore()
        return {"status": "ok", "title": w.title}

    async def launch_app(self, command: str) -> dict[str, Any]:
        """Launch application via shell. Requires confirmation in agent layer."""
        try:
            subprocess.Popen(command, shell=True)
            return {"status": "ok", "command": command}
        except Exception as e:
            return {"status": "error", "message": str(e)}
