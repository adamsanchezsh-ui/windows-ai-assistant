"""User profiles: Gaming, School, Privacy, Work."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserProfile:
    id: str
    name: str
    description: str = ""
    # Feature toggles
    overlay: bool = False
    voice: bool = False
    voice_hints: bool = False
    wake_word: bool = False
    vision_mode: str = "off"  # off | on_demand | periodic
    performance_mode: str = "balanced"
    ai_style: str = "normal"
    school_difficulty: str = "normal"  # simple | normal | detailed
    web_research: bool = True
    automation: bool = True
    dnd: bool = False  # do not disturb
    extra: dict[str, Any] = field(default_factory=dict)


PROFILES: dict[str, UserProfile] = {
    "gaming": UserProfile(
        id="gaming",
        name="Gaming",
        description="Overlay, performance, voice hints, herní rady",
        overlay=True,
        voice=True,
        voice_hints=True,
        wake_word=True,
        vision_mode="on_demand",
        performance_mode="performance",
        ai_style="brief",
        web_research=False,
        dnd=True,
    ),
    "school": UserProfile(
        id="school",
        name="School",
        description="Výuka, jednoduché vysvětlování, research podle potřeby",
        overlay=False,
        voice=False,
        wake_word=False,
        vision_mode="on_demand",
        performance_mode="balanced",
        ai_style="simple",
        school_difficulty="simple",
        web_research=True,
        dnd=False,
    ),
    "privacy": UserProfile(
        id="privacy",
        name="Privacy",
        description="Vision OFF, mikrofon OFF, wake word OFF, automation OFF",
        overlay=False,
        voice=False,
        voice_hints=False,
        wake_word=False,
        vision_mode="off",
        performance_mode="balanced",
        ai_style="normal",
        web_research=False,
        automation=False,
        dnd=True,
    ),
    "work": UserProfile(
        id="work",
        name="Work",
        description="Produktivita, notifikace, web research",
        overlay=False,
        voice=True,
        wake_word=True,
        vision_mode="on_demand",
        performance_mode="balanced",
        ai_style="professional",
        web_research=True,
        dnd=False,
    ),
    "default": UserProfile(
        id="default",
        name="Default",
        description="Výchozí vyvážený profil",
        overlay=False,
        voice=False,
        wake_word=False,
        vision_mode="on_demand",
        performance_mode="balanced",
        ai_style="normal",
        web_research=True,
    ),
}


def get_profile(profile_id: str) -> UserProfile:
    return PROFILES.get(profile_id, PROFILES["default"])
