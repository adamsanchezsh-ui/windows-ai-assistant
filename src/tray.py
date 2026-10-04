"""System tray icon for CYPHERpc (optional pystray)."""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None  # type: ignore
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


def _default_icon(size: int = 64):
    if Image is None:
        return None
    img = Image.new("RGB", (size, size), color=(124, 58, 237))
    d = ImageDraw.Draw(img)
    d.ellipse([12, 12, size - 12, size - 12], fill=(255, 255, 255))
    d.text((size // 2 - 6, size // 2 - 8), "C", fill=(124, 58, 237))
    return img


class TrayApp:
    def __init__(
        self,
        on_show: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
        on_privacy: Callable[[], None] | None = None,
        on_cc: Callable[[], None] | None = None,
    ):
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_privacy = on_privacy
        self.on_cc = on_cc
        self._icon = None

    def start(self) -> None:
        if pystray is None:
            logger.warning("pystray not installed – tray disabled")
            return
        menu = pystray.Menu(
            pystray.MenuItem("Otevřít CYPHERpc", lambda: self.on_show and self.on_show()),
            pystray.MenuItem("Control Center", lambda: self.on_cc and self.on_cc()),
            pystray.MenuItem("Privacy Mode", lambda: self.on_privacy and self.on_privacy()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ukončit", lambda: self.on_quit and self.on_quit()),
        )
        self._icon = pystray.Icon("CYPHERpc", _default_icon(), "CYPHERpc", menu)
        # Non-blocking in thread
        import threading
        threading.Thread(target=self._icon.run, daemon=True).start()
        logger.info("Tray icon started")

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
