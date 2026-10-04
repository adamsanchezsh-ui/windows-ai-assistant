"""Voice: wake word 'Cypher', STT, TTS, mic/voice selection, PTT, privacy."""

from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    "cs", "en", "de", "sk", "pl", "es", "fr", "it", "ja", "ko",
]

WAKE_WORD = "cypher"


class VoiceService:
    """
    Hlasový modul CYPHERpc.
    Wake word: „Cypher“
    Placeholder pro STT/TTS – napojitelné na edge-tts, Whisper, Windows SAPI.
    """

    def __init__(
        self,
        language: str = "cs",
        volume: float = 0.8,
        rate: float = 1.0,
        enabled: bool = False,
        wake_word_enabled: bool = False,
    ):
        self.language = language if language in SUPPORTED_LANGUAGES else "cs"
        self.volume = max(0.0, min(1.0, volume))
        self.rate = rate
        self.enabled = enabled
        self.hints_enabled = True
        self.wake_word_enabled = wake_word_enabled
        self.push_to_talk = False
        self.listening = False  # visual mic indicator
        self.selected_microphone: str | None = None
        self.selected_voice: str | None = None
        self.privacy_blocked = False
        self._on_command: Callable[[str], Awaitable[None]] | None = None

    def set_command_handler(self, cb: Callable[[str], Awaitable[None]]) -> None:
        self._on_command = cb

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        if not self.enabled:
            self.listening = False
        return self.enabled

    def toggle_hints(self) -> bool:
        self.hints_enabled = not self.hints_enabled
        return self.hints_enabled

    def toggle_wake_word(self) -> bool:
        self.wake_word_enabled = not self.wake_word_enabled
        return self.wake_word_enabled

    def set_language(self, lang: str) -> None:
        if lang in SUPPORTED_LANGUAGES:
            self.language = lang

    def set_privacy(self, blocked: bool) -> None:
        self.privacy_blocked = blocked
        if blocked:
            self.listening = False
            self.wake_word_enabled = False

    def list_microphones(self) -> list[str]:
        # Placeholder – integrate sounddevice / pyaudio
        return ["Default Microphone", "Headset Mic", "Array Mic"]

    def list_voices(self) -> list[str]:
        return ["cs-CZ-Antonin", "cs-CZ-Vlasta", "en-US-Jenny", "en-US-Guy"]

    def set_microphone(self, name: str) -> None:
        self.selected_microphone = name

    def set_voice(self, name: str) -> None:
        self.selected_voice = name

    async def speak(self, text: str) -> dict[str, Any]:
        if not self.enabled or not self.hints_enabled or self.privacy_blocked:
            return {"status": "skipped", "reason": "voice disabled or privacy"}
        logger.info("[TTS %s vol=%.1f] %s", self.language, self.volume, text[:100])
        # Integrate edge-tts / pyttsx3 here
        return {"status": "ok", "text": text, "language": self.language}

    async def listen(self, timeout: float = 5.0) -> str:
        if not self.enabled or self.privacy_blocked:
            return ""
        self.listening = True
        try:
            logger.info("Listening (timeout=%.1fs, mic=%s)...", timeout, self.selected_microphone)
            # Integrate speech_recognition / whisper here
            return ""
        finally:
            self.listening = False

    async def process_audio_text(self, text: str) -> str | None:
        """
        Pokud je wake word zapnuté, čeká na 'Cypher' a pak předá zbytek příkazu.
        """
        if self.privacy_blocked:
            return None
        t = text.strip().lower()
        if self.wake_word_enabled:
            if WAKE_WORD in t:
                # Remove wake word, rest is command
                cmd = t.replace(WAKE_WORD, "", 1).strip(" ,.")
                if cmd and self._on_command:
                    await self._on_command(cmd)
                return cmd or None
            return None
        # Without wake word, treat whole text as command if listening/PTT
        if self.listening or self.push_to_talk:
            if self._on_command:
                await self._on_command(t)
            return t
        return None

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "wake_word": self.wake_word_enabled,
            "wake_word_phrase": WAKE_WORD,
            "listening": self.listening,
            "hints": self.hints_enabled,
            "language": self.language,
            "volume": self.volume,
            "rate": self.rate,
            "microphone": self.selected_microphone,
            "voice": self.selected_voice,
            "push_to_talk": self.push_to_talk,
            "privacy_blocked": self.privacy_blocked,
        }
