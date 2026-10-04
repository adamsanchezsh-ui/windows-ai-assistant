"""Screen capture, OCR and vision helpers."""

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
    """Capture screenshots, run OCR, support multi-monitor."""

    def __init__(
        self,
        data_dir: Path,
        vision_mode: Literal["off", "on_demand", "periodic"] = "on_demand",
        selected_monitor: int = 1,
        privacy_mode: bool = False,
    ):
        self.data_dir = data_dir
        self.vision_mode = vision_mode
        self.selected_monitor = selected_monitor  # 1-based
        self.privacy_mode = privacy_mode
        self._last_screenshot: Path | None = None

    def set_privacy(self, enabled: bool) -> None:
        self.privacy_mode = enabled

    def set_monitor(self, monitor: int) -> None:
        if 1 <= monitor <= 4:
            self.selected_monitor = monitor

    def _guard(self) -> None:
        if self.privacy_mode:
            raise RuntimeError("Privacy Mode is active – screen capture disabled")
        if self.vision_mode == "off":
            raise RuntimeError("Vision mode is OFF")

    def list_monitors(self) -> list[dict[str, Any]]:
        if mss is None:
            return [{"id": 1, "width": 1920, "height": 1080}]
        with mss.mss() as sct:
            # monitors[0] is virtual all-in-one; 1..n are physical
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
            # Fallback: full screen via PIL (single monitor)
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
        logger.info("Screenshot saved: %s", path)
        return path

    def ocr(self, image_path: Path | None = None, lang: str = "ces+eng") -> str:
        self._guard()
        if pytesseract is None:
            return "[OCR not available – install pytesseract + Tesseract]"
        path = image_path or self._last_screenshot
        if not path or not path.exists():
            path = self.capture()
        img = Image.open(path)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()

    def analyze_placeholder(self, image_path: Path | None = None) -> dict[str, Any]:
        """Placeholder for full vision model analysis."""
        path = image_path or self._last_screenshot
        if not path:
            path = self.capture()
        text = self.ocr(path)
        return {
            "path": str(path),
            "ocr_preview": text[:500],
            "note": "Pro plnou AI analýzu předej obrázek vision modelu přes agent.",
        }
