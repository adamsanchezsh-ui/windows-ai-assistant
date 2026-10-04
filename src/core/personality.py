"""Response style / personality settings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Style(str, Enum):
    BRIEF = "brief"          # stručný
    NORMAL = "normal"
    DETAILED = "detailed"    # podrobný
    TECHNICAL = "technical"
    SIMPLE = "simple"        # jednoduchý (School)
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class LanguageLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Personality:
    style: Style = Style.NORMAL
    language: str = "cs"
    language_level: LanguageLevel = LanguageLevel.INTERMEDIATE
    length_preference: str = "medium"  # short | medium | long
    humor: bool = False
    name: str = "CYPHERpc"

    def system_addon(self) -> str:
        parts = [
            f"Tvoje jméno je {self.name}.",
            f"Styl odpovědí: {self.style.value}.",
            f"Jazyk: {self.language}.",
            f"Technická úroveň: {self.language_level.value}.",
            f"Délka odpovědí: {self.length_preference}.",
        ]
        if self.style == Style.BRIEF:
            parts.append("Odpovídej maximálně stručně – 1–3 věty, pokud to stačí.")
        elif self.style == Style.DETAILED:
            parts.append("Vysvětluj podrobně, s příklady a kontextem.")
        elif self.style == Style.SIMPLE:
            parts.append("Vysvětluj jednoduše, jako bys mluvil k začátečníkovi.")
        elif self.style == Style.TECHNICAL:
            parts.append("Používej přesné technické termíny, uváděj detaily implementace.")
        if self.humor:
            parts.append("Můžeš být lehce vtipný, ale zůstaň užitečný.")
        return " ".join(parts)
