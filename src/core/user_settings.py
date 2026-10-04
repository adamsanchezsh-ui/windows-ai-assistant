"""
CYPHERpc user settings – inspired by Grok / ChatGPT custom instructions.

Uživatel si nastaví:
- jak má AI odpovídat (styl, délka, tón)
- co o sobě AI ví (jméno, zájmy, úroveň)
- vlastní instrukce (custom instructions)
- chování (humor, přímost, emoji, …)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AboutUser:
    """Co má AI vědět o uživateli (jako ChatGPT Custom Instructions – about you)."""
    name: str = ""
    nickname: str = ""
    language: str = "cs"
    occupation: str = ""
    interests: list[str] = field(default_factory=list)
    tech_level: str = "intermediate"  # beginner | intermediate | advanced | expert
    notes: str = ""  # volný text – cokoliv důležitého


@dataclass
class ResponseStyle:
    """Jak má AI odpovídat (jako Grok personality / ChatGPT style)."""
    style: str = "normal"  # brief | normal | detailed | technical | simple | friendly | professional
    length: str = "medium"  # short | medium | long | unbounded
    tone: str = "helpful"  # helpful | casual | formal | witty | direct
    humor: bool = True
    emoji: bool = False
    use_markdown: bool = True
    show_reasoning: bool = False  # ukazovat myšlenkový postup
    cite_sources: bool = True
    language: str = "cs"  # odpovědi v tomto jazyce (auto = podle uživatele)
    formality: str = "tykani"  # tykani | vykani


@dataclass
class Behavior:
    """Chování asistenta."""
    name: str = "CYPHERpc"  # jak se AI představuje
    personality_blurb: str = (
        "Jsi CYPHERpc – chytrý, přímý a užitečný AI asistent pro Windows. "
        "Odpovídáš jako moderní AI (ChatGPT/Claude/úroveň Grok): přesně, s nadhledem, bez zbytečného omáčení."
    )
    custom_instructions: str = ""  # vlastní instrukce uživatele (max prakticky neomezeno)
    avoid: str = ""  # čemu se vyhnout (např. "nezmíňuj politiku")
    always_do: str = ""  # co dělat vždy (např. "odpovídej česky", "buď stručný")
    proactive: bool = True  # navrhovat další kroky
    ask_clarifying: bool = True  # ptát se, když je dotaz nejasný
    safety_confirmations: bool = True  # potvrzení rizikových akcí


@dataclass
class FeaturePrefs:
    """Preference funkcí."""
    web_search_default: bool = True
    memory_enabled: bool = False
    voice_enabled: bool = False
    wake_word: bool = False
    vision_mode: str = "on_demand"
    auto_model_select: bool = True
    stream_responses: bool = True
    save_chat_history: bool = True


@dataclass
class UserSettings:
    about: AboutUser = field(default_factory=AboutUser)
    response: ResponseStyle = field(default_factory=ResponseStyle)
    behavior: Behavior = field(default_factory=Behavior)
    features: FeaturePrefs = field(default_factory=FeaturePrefs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "about": asdict(self.about),
            "response": asdict(self.response),
            "behavior": asdict(self.behavior),
            "features": asdict(self.features),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserSettings":
        return cls(
            about=AboutUser(**data.get("about", {})),
            response=ResponseStyle(**data.get("response", {})),
            behavior=Behavior(**data.get("behavior", {})),
            features=FeaturePrefs(**data.get("features", {})),
        )

    def build_system_addon(self) -> str:
        """Sestaví blok pro system prompt – jako Grok/ChatGPT custom instructions."""
        parts: list[str] = []

        # Identita
        parts.append(f"Tvoje jméno je {self.behavior.name}.")
        if self.behavior.personality_blurb:
            parts.append(self.behavior.personality_blurb)

        # O uživateli
        about_bits = []
        if self.about.name:
            about_bits.append(f"jméno uživatele: {self.about.name}")
        if self.about.nickname:
            about_bits.append(f"přezdívka: {self.about.nickname}")
        if self.about.occupation:
            about_bits.append(f"profese: {self.about.occupation}")
        if self.about.interests:
            about_bits.append(f"zájmy: {', '.join(self.about.interests)}")
        if self.about.tech_level:
            about_bits.append(f"technická úroveň: {self.about.tech_level}")
        if self.about.notes:
            about_bits.append(f"poznámky: {self.about.notes}")
        if about_bits:
            parts.append("O uživateli: " + "; ".join(about_bits) + ".")

        # Styl odpovědí
        r = self.response
        parts.append(
            f"Styl: {r.style}. Délka: {r.length}. Tón: {r.tone}. "
            f"Jazyk odpovědí: {r.language}. Oslovení: {r.formality}."
        )
        if r.style == "brief":
            parts.append("Odpovídej maximálně stručně – jen to podstatné.")
        elif r.style == "detailed":
            parts.append("Vysvětluj podrobně, s příklady a kontextem.")
        elif r.style == "simple":
            parts.append("Vysvětluj jednoduše, bez žargonu.")
        elif r.style == "technical":
            parts.append("Používej přesné technické termíny a detaily.")
        if r.length == "short":
            parts.append("Preferuj krátké odpovědi.")
        elif r.length == "long" or r.length == "unbounded":
            parts.append("Můžeš odpovídat dlouze, pokud to téma vyžaduje – žádný umělý limit délky.")
        if r.humor:
            parts.append("Můžeš být vtipný a s nadhledem (jako Grok), ale zůstaň užitečný.")
        if not r.emoji:
            parts.append("Nepoužívej emoji, pokud to uživatel výslovně nechce.")
        if r.show_reasoning:
            parts.append("U složitějších otázek ukaž stručně myšlenkový postup.")
        if r.cite_sources:
            parts.append("U faktů z webu uváděj zdroje.")
        if r.use_markdown:
            parts.append("Formátuj odpovědi v Markdownu, kde to dává smysl.")

        # Vlastní instrukce
        if self.behavior.custom_instructions.strip():
            parts.append("Vlastní instrukce uživatele:\n" + self.behavior.custom_instructions.strip())
        if self.behavior.always_do.strip():
            parts.append("Vždy: " + self.behavior.always_do.strip())
        if self.behavior.avoid.strip():
            parts.append("Vyhni se: " + self.behavior.avoid.strip())

        if self.behavior.proactive:
            parts.append("Kde to dává smysl, navrhni další užitečný krok.")
        if self.behavior.ask_clarifying:
            parts.append("Když je dotaz nejasný, zeptej se upřesňující otázku.")

        return "\n".join(parts)


class UserSettingsStore:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "user_settings.json"
        self.settings = UserSettings()
        self.load()

    def load(self) -> UserSettings:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.settings = UserSettings.from_dict(data)
            except Exception:
                logger.exception("Failed to load user settings")
        return self.settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update(self, **kwargs: Any) -> UserSettings:
        """
        Flat update helpers, e.g.:
          update(name="Adam", style="brief", humor=True, custom_instructions="...")
        """
        s = self.settings
        about_keys = {"name", "nickname", "language", "occupation", "interests", "tech_level", "notes"}
        response_keys = {
            "style", "length", "tone", "humor", "emoji", "use_markdown",
            "show_reasoning", "cite_sources", "formality",
        }
        # response.language vs about.language
        behavior_keys = {
            "assistant_name", "personality_blurb", "custom_instructions",
            "avoid", "always_do", "proactive", "ask_clarifying", "safety_confirmations",
        }
        feature_keys = {
            "web_search_default", "memory_enabled", "voice_enabled", "wake_word",
            "vision_mode", "auto_model_select", "stream_responses", "save_chat_history",
        }

        for k, v in kwargs.items():
            if k == "assistant_name":
                s.behavior.name = str(v)
            elif k == "response_language":
                s.response.language = str(v)
            elif k in about_keys:
                if k == "interests" and isinstance(v, str):
                    v = [x.strip() for x in v.split(",") if x.strip()]
                setattr(s.about, k, v)
            elif k in response_keys:
                setattr(s.response, k, v)
            elif k in behavior_keys:
                setattr(s.behavior, k if k != "assistant_name" else "name", v)
            elif k in feature_keys:
                setattr(s.features, k, v)
            elif k == "custom_instructions":
                s.behavior.custom_instructions = str(v)

        self.save()
        return s

    def reset(self) -> UserSettings:
        self.settings = UserSettings()
        self.save()
        return self.settings

    def summary(self) -> str:
        s = self.settings
        lines = [
            f"Asistent: {s.behavior.name}",
            f"Uživatel: {s.about.name or '(nenastaveno)'} | úroveň: {s.about.tech_level}",
            f"Styl: {s.response.style} | délka: {s.response.length} | tón: {s.response.tone}",
            f"Jazyk: {s.response.language} | {s.response.formality}",
            f"Humor: {s.response.humor} | emoji: {s.response.emoji} | reasoning: {s.response.show_reasoning}",
            f"Paměť: {s.features.memory_enabled} | voice: {s.features.voice_enabled} | wake: {s.features.wake_word}",
            f"Vision: {s.features.vision_mode} | auto-model: {s.features.auto_model_select}",
        ]
        if s.behavior.custom_instructions:
            preview = s.behavior.custom_instructions[:120].replace("\n", " ")
            lines.append(f"Custom instructions: {preview}…")
        if s.about.notes:
            lines.append(f"Poznámky: {s.about.notes[:100]}")
        return "\n".join(lines)
