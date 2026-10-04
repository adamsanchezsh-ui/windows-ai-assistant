"""Voice input/output (TTS/STT) with multi-language support."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    "cs", "en", "de", "sk", "pl", "es", "fr", "it", "ja", "ko"
]


class VoiceService:
    """Text-to-speech and speech-to-text abstraction."""

    def __init__(
        self,
        language: str = "cs",
        volume: float = 0.8,
        rate: float = 1.0,
        enabled: bool = False,
    ):
        self.language = language if language in SUPPORTED_LANGUAGES else "cs"
        self.volume = volume
        self.rate = rate
        self.enabled = enabled
        self.hints_enabled = True
        self._tts = None

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def toggle_hints(self) -> bool:
        self.hints_enabled = not self.hints_enabled
        return self.hints_enabled

    def set_language(self, lang: str) -> None:
        if lang in SUPPORTED_LANGUAGES:
            self.language = lang

    async def speak(self, text: str) -> dict[str, Any]:
        if not self.enabled or not self.hints_enabled:
            return {"status": "skipped", "reason": "voice or hints disabled"}
        # Placeholder: integrate edge-tts / pyttsx3 / system SAPI
        logger.info("[TTS %s] %s", self.language, text[:80])
        return {"status": "ok", "text": text, "language": self.language}

    async def listen(self, timeout: float = 5.0) -> str:
        if not self.enabled:
            return ""
        # Placeholder for STT (speech_recognition / whisper)
        logger.info("Listening (timeout=%.1fs)...", timeout)
        return ""
