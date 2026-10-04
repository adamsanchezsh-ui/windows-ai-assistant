"""Smart clipboard assistant."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import pyperclip
except ImportError:
    pyperclip = None  # type: ignore


class SmartClipboard:
    def get(self) -> str:
        if pyperclip is None:
            return ""
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def set(self, text: str) -> None:
        if pyperclip is None:
            return
        pyperclip.copy(text)

    def summarize_request(self, text: str) -> str:
        return f"Shrň následující text:\n\n{text}"

    def fix_request(self, text: str) -> str:
        return f"Oprav gramatiku a styl následujícího textu:\n\n{text}"

    def translate_request(self, text: str, target: str = "en") -> str:
        return f"Přelož do jazyka {target}:\n\n{text}"

    def extract_request(self, text: str) -> str:
        return f"Extrahuj důležité údaje (data, čísla, jména, odkazy) z textu:\n\n{text}"
