"""
CYPHERpc voice – wake word Cypher, STT/TTS.
Hlasy ve stylu Grok: přímé, s nadhledem, bez zbytečného omáčení.
TTS: edge-tts (online) / pyttsx3 (offline fallback).
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = [
    "cs", "en", "de", "sk", "pl", "es", "fr", "it", "ja", "ko",
]

WAKE_WORD = "cypher"

# Grok-like voice personas (edge-tts voice ids + style hints)
GROK_VOICES: dict[str, dict[str, str]] = {
    "grok_cs": {
        "id": "cs-CZ-AntoninNeural",
        "label": "Grok CS (muž)",
        "lang": "cs",
        "style": "Přímý, klidný, s lehkým nadhledem. Krátké věty.",
    },
    "grok_cs_f": {
        "id": "cs-CZ-VlastaNeural",
        "label": "Grok CS (žena)",
        "lang": "cs",
        "style": "Jasná, přátelská, bez zbytečného omáčení.",
    },
    "grok_en": {
        "id": "en-US-AndrewNeural",
        "label": "Grok EN (male)",
        "lang": "en",
        "style": "Direct, dry wit, concise — Grok energy.",
    },
    "grok_en_f": {
        "id": "en-US-JennyNeural",
        "label": "Grok EN (female)",
        "lang": "en",
        "style": "Clear, smart, slightly playful.",
    },
    "grok_de": {
        "id": "de-DE-ConradNeural",
        "label": "Grok DE",
        "lang": "de",
        "style": "Direkt, ruhig, mit Augenzwinkern.",
    },
    "grok_sk": {
        "id": "sk-SK-LukasNeural",
        "label": "Grok SK",
        "lang": "sk",
        "style": "Priamy, s nadhľadom.",
    },
}


@dataclass
class VoicePersona:
    key: str
    tts_id: str
    label: str
    lang: str
    style: str


def list_grok_personas() -> list[VoicePersona]:
    return [
        VoicePersona(key=k, tts_id=v["id"], label=v["label"], lang=v["lang"], style=v["style"])
        for k, v in GROK_VOICES.items()
    ]


class VoiceService:
    """
    Hlas CYPHERpc.
    - Wake word: Cypher
    - Default persona: grok_cs (Grok-like Czech male)
    - edge-tts pokud je nainstalované, jinak pyttsx3 / log only
    """

    def __init__(
        self,
        language: str = "cs",
        volume: float = 0.85,
        rate: float = 1.05,  # mírně svižnější = Grok feel
        enabled: bool = False,
        wake_word_enabled: bool = False,
        persona: str = "grok_cs",
    ):
        self.language = language if language in SUPPORTED_LANGUAGES else "cs"
        self.volume = max(0.0, min(1.0, volume))
        self.rate = rate
        self.enabled = enabled
        self.hints_enabled = True
        self.wake_word_enabled = wake_word_enabled
        self.push_to_talk = False
        self.listening = False
        self.selected_microphone: str | None = None
        self.persona_key = persona if persona in GROK_VOICES else "grok_cs"
        self.privacy_blocked = False
        self._on_command: Callable[[str], Awaitable[None]] | None = None
        self._edge_available: bool | None = None

    # --- persona / Grok voice ---
    def set_persona(self, key: str) -> str:
        if key not in GROK_VOICES:
            return f"Neznámá persona. Dostupné: {', '.join(GROK_VOICES)}"
        self.persona_key = key
        self.language = GROK_VOICES[key]["lang"]
        return f"Hlas: {GROK_VOICES[key]['label']}"

    def current_persona(self) -> VoicePersona:
        v = GROK_VOICES[self.persona_key]
        return VoicePersona(
            key=self.persona_key,
            tts_id=v["id"],
            label=v["label"],
            lang=v["lang"],
            style=v["style"],
        )

    def voice_style_addon(self) -> str:
        """Krátký hint do system promptu – jak má znít mluvená odpověď."""
        p = self.current_persona()
        return (
            f"Když generuješ text pro hlasité čtení: {p.style} "
            f"Bez markdownu, bez odrážek, přirozené věty. Max ~2 krátké odstavce."
        )

    # --- toggles ---
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
            # auto-pick matching Grok persona
            for k, v in GROK_VOICES.items():
                if v["lang"] == lang:
                    self.persona_key = k
                    break

    def set_privacy(self, blocked: bool) -> None:
        self.privacy_blocked = blocked
        if blocked:
            self.listening = False
            self.wake_word_enabled = False

    def set_command_handler(self, cb: Callable[[str], Awaitable[None]]) -> None:
        self._on_command = cb

    def list_microphones(self) -> list[str]:
        try:
            import sounddevice as sd  # type: ignore
            devices = sd.query_devices()
            return [
                f"{i}: {d['name']}"
                for i, d in enumerate(devices)
                if d["max_input_channels"] > 0
            ]
        except Exception:
            return ["Default Microphone"]

    def list_voices(self) -> list[str]:
        return [f"{k}: {v['label']}" for k, v in GROK_VOICES.items()]

    def _has_edge_tts(self) -> bool:
        if self._edge_available is None:
            try:
                import edge_tts  # noqa: F401
                self._edge_available = True
            except ImportError:
                self._edge_available = False
        return self._edge_available

    async def speak(self, text: str) -> dict[str, Any]:
        if not self.enabled or not self.hints_enabled or self.privacy_blocked:
            return {"status": "skipped", "reason": "voice disabled or privacy"}

        # Strip markdown for speech
        clean = (
            text.replace("**", "")
            .replace("__", "")
            .replace("`", "")
            .replace("#", "")
        )
        # Keep spoken answers Grok-short
        if len(clean) > 800:
            clean = clean[:800].rsplit(" ", 1)[0] + "…"

        persona = self.current_persona()
        logger.info("[TTS %s] %s", persona.label, clean[:100])

        if self._has_edge_tts():
            try:
                import edge_tts
                communicate = edge_tts.Communicate(clean, persona.tts_id, rate=f"{int((self.rate - 1) * 100):+}%")
                out = Path(tempfile.gettempdir()) / "cypherpc_tts.mp3"
                await communicate.save(str(out))
                # Play if possible
                try:
                    import pygame
                    pygame.mixer.init()
                    pygame.mixer.music.load(str(out))
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                except Exception:
                    # Windows: start default player non-blocking
                    try:
                        import os
                        os.startfile(str(out))  # type: ignore
                    except Exception:
                        pass
                return {"status": "ok", "engine": "edge-tts", "voice": persona.label, "file": str(out)}
            except Exception as e:
                logger.warning("edge-tts failed: %s", e)

        # Offline fallback
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", int(180 * self.rate))
            engine.setProperty("volume", self.volume)
            engine.say(clean)
            engine.runAndWait()
            return {"status": "ok", "engine": "pyttsx3", "voice": persona.label}
        except Exception as e:
            logger.info("TTS fallback log only: %s", e)
            return {"status": "logged", "text": clean, "voice": persona.label}

    async def listen(self, timeout: float = 5.0) -> str:
        if not self.enabled or self.privacy_blocked:
            return ""
        self.listening = True
        try:
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source, duration=0.3)
                    audio = r.listen(source, timeout=timeout, phrase_time_limit=15)
                # Google free STT as default; Whisper optional
                try:
                    text = r.recognize_google(audio, language="cs-CZ" if self.language == "cs" else "en-US")
                except Exception:
                    text = r.recognize_google(audio)
                return text or ""
            except Exception as e:
                logger.warning("STT unavailable: %s", e)
                return ""
        finally:
            self.listening = False

    async def process_audio_text(self, text: str) -> str | None:
        if self.privacy_blocked:
            return None
        t = text.strip().lower()
        if self.wake_word_enabled:
            if WAKE_WORD in t:
                cmd = t.replace(WAKE_WORD, "", 1).strip(" ,.")
                if cmd and self._on_command:
                    await self._on_command(cmd)
                return cmd or None
            return None
        if self.listening or self.push_to_talk:
            if self._on_command:
                await self._on_command(t)
            return t
        return None

    def status(self) -> dict[str, Any]:
        p = self.current_persona()
        return {
            "enabled": self.enabled,
            "wake_word": self.wake_word_enabled,
            "wake_word_phrase": WAKE_WORD,
            "listening": self.listening,
            "hints": self.hints_enabled,
            "language": self.language,
            "volume": self.volume,
            "rate": self.rate,
            "persona": p.key,
            "persona_label": p.label,
            "tts_voice": p.tts_id,
            "microphone": self.selected_microphone,
            "push_to_talk": self.push_to_talk,
            "privacy_blocked": self.privacy_blocked,
            "edge_tts": self._has_edge_tts(),
        }
