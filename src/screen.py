"""Screen capture, OCR, region select, multi-monitor – no hard limits."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from PIL import Image

logger = logging.getLogger(__name__)

try:
    import mss
    import mss.tools
except ImportError:
    mss = None  # type: ignore

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore


class ScreenService:
    def __init__(
        self,
        data_dir: Path,
        vision_mode: Literal["off", "on_demand", "periodic"] = "on_demand",
        selected_monitor: int = 1,
        privacy_mode: bool = False,
    ):
        self.data_dir = data_dir
        self.vision_mode = vision_mode
        self.selected_monitor = selected_monitor
        self.privacy_mode = privacy_mode
        self._last_screenshot: Path | None = None

    def set_privacy(self, enabled: bool) -> None:
        self.privacy_mode = enabled

    def set_monitor(self, monitor: int) -> None:
        if monitor >= 1:
            self.selected_monitor = monitor  # no hard max of 4 – support all detected

    def _guard(self) -> None:
        if self.privacy_mode:
            raise RuntimeError("Privacy Mode – screen capture disabled")
        if self.vision_mode == "off":
            raise RuntimeError("Vision mode is OFF")

    def list_monitors(self) -> list[dict[str, Any]]:
        if mss is None:
            return [{"id": 1, "width": 1920, "height": 1080}]
        with mss.mss() as sct:
            return [
                {"id": i, "left": m["left"], "top": m["top"], "width": m["width"], "height": m["height"]}
                for i, m in enumerate(sct.monitors[1:], start=1)
            ]

    def capture(self, monitor: int | None = None) -> Path:
        self._guard()
        mon = monitor or self.selected_monitor
        out = self.data_dir / "screenshots"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"screen_m{mon}.png"

        if mss is None:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(path)
        else:
            with mss.mss() as sct:
                monitors = sct.monitors
                if mon < 1 or mon >= len(monitors):
                    mon = 1
                shot = sct.grab(monitors[mon])
                mss.tools.to_png(shot.rgb, shot.size, output=str(path))

        self._last_screenshot = path
        logger.info("Screenshot: %s", path)
        return path

    def capture_region(self, left: int, top: int, width: int, height: int) -> Path:
        """Capture specific region of the virtual screen."""
        self._guard()
        out = self.data_dir / "screenshots"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "screen_region.png"
        region = {"left": left, "top": top, "width": width, "height": height}

        if mss is None:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=(left, top, left + width, top + height))
            img.save(path)
        else:
            with mss.mss() as sct:
                shot = sct.grab(region)
                mss.tools.to_png(shot.rgb, shot.size, output=str(path))

        self._last_screenshot = path
        return path

    def ocr(self, image_path: Path | None = None, lang: str = "ces+eng") -> str:
        self._guard()
        if pytesseract is None:
            return "[OCR unavailable – install pytesseract + Tesseract OCR]"
        path = image_path or self._last_screenshot
        if not path or not path.exists():
            path = self.capture()
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang=lang).strip()

    def analyze_placeholder(self, image_path: Path | None = None) -> dict[str, Any]:
        path = image_path or self._last_screenshot
        if not path:
            path = self.capture()
        text = self.ocr(path)
        return {
            "path": str(path),
            "ocr": text,  # full OCR text, no truncation
            "note": "Pro plnou vision analýzu předej obrázek modelu s vision podporou.",
        }
