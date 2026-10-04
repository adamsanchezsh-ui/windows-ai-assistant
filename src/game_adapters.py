"""Game-specific adapters – advisory helpers only (no cheating)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.game_profiles import GameProfile, get_profile

logger = logging.getLogger(__name__)


@dataclass
class HealAdvice:
    should_heal: bool
    urgency: str
    message: str
    preferred_items: list[str]


@dataclass
class RotationAdvice:
    direction: str
    reason: str
    priority: str
    tips: list[str]


@dataclass
class PositionAdvice:
    suggestion: str
    high_ground: bool
    cover: str
    risk: str


class FortniteAdapter:
    DROP_TIPS = {
        "aggressive": [
            "Hot drop na populární POI – očekávej early fights.",
            "Snaž se rychle sebrat zbraň a materials, pak třetí stranu.",
            "Pokud padá hodně lidí, zvaž edge téhož POI místo středu.",
        ],
        "balanced": [
            "Středně populární POI s dobrým lootem a únikem do zóny.",
            "Loot 1–2 budovy, pak rotuj směrem k zóně.",
            "Drž se blízko coveru (budovy, skály).",
        ],
        "passive": [
            "Klidnější okraj mapy / menší POI.",
            "Full loot + shield, pak pomalá rotace edge zóny.",
            "Vyhýbej se early fightům, hraj o placement.",
        ],
    }

    HEAL_PRIORITY = [
        "Chug Splash", "Shield Potion", "Big Shield Potion",
        "Medkit", "Bandages", "Fish / Food",
    ]

    def __init__(self, profile: GameProfile | None = None):
        self.profile = profile or get_profile("fortnite")
        thresholds = (self.profile.extra or {}).get("heal_thresholds", {}) if self.profile else {}
        self.critical_hp = thresholds.get("critical_hp", 30)
        self.low_hp = thresholds.get("low_hp", 50)
        self.low_shield = thresholds.get("low_shield", 50)
        self.pre_rotate_min_shield = thresholds.get("pre_rotate_min_shield", 50)

    def heal_advice(
        self,
        hp: int | None = None,
        shield: int | None = None,
        in_combat: bool = False,
        about_to_rotate: bool = False,
        has_heals: bool = True,
    ) -> HealAdvice:
        if hp is None and shield is None:
            return HealAdvice(
                False, "none",
                "Nevím aktuální HP/shield – řekni mi stav (např. /heal 40) nebo zapni vision.",
                self.HEAL_PRIORITY,
            )
        hp = hp if hp is not None else 100
        shield = shield if shield is not None else 0
        if not has_heals:
            return HealAdvice(False, "none", "Nemáš healy – hledej loot.", self.HEAL_PRIORITY)
        if in_combat and hp > self.critical_hp:
            return HealAdvice(False, "low", "Jsi ve fightu – heal až po něm (nebo do boxu).", self.HEAL_PRIORITY)
        if hp <= self.critical_hp:
            return HealAdvice(True, "critical", f"KRITICKÉ HP ({hp})! Okamžitě heal, schovej se.", ["Medkit", "Bandages", "Chug Splash"])
        if hp <= self.low_hp:
            return HealAdvice(True, "high", f"Nízké HP ({hp}) – heal co nejdřív v bezpečí.", ["Medkit", "Bandages"])
        if about_to_rotate and shield < self.pre_rotate_min_shield:
            return HealAdvice(True, "medium", f"Před rotací doplň shield (máš {shield}).", ["Shield Potion", "Chug Splash"])
        if shield < self.low_shield and not in_combat:
            return HealAdvice(True, "medium", f"Nízký shield ({shield}) – popni Shield Pot.", ["Shield Potion", "Chug Splash"])
        return HealAdvice(False, "none", f"HP/shield OK ({hp}/{shield}). Šetři healy.", self.HEAL_PRIORITY)

    def rotation_advice(
        self,
        zone_closing: bool = False,
        has_mobility: bool = False,
        near_fight: bool = False,
        materials: int | None = None,
        style: str = "balanced",
    ) -> RotationAdvice:
        tips: list[str] = []
        if zone_closing:
            tips.append("Storm se zavírá – prioritizuj cestu do zóny.")
            tips.append("Použij mobility, pokud máš; jinak edge + cover.")
            return RotationAdvice("do zóny (edge)", "Storm pressure", "safe", tips)
        if near_fight:
            tips.append("Blízký fight – third-party nebo ústup.")
            return RotationAdvice("k fightu opatrně nebo pryč", "Third-party", "balanced", tips)
        tips.append("Rotuj k další zóně, preferuj high ground a cover.")
        tips.append("Vyhni se dlouhému běhu přes open field.")
        if materials is not None and materials < 100:
            tips.append(f"Málo materials ({materials}) – farmi cestou.")
        return RotationAdvice("edge zóny / high ground", "Mid-game rotace", style if style in ("safe", "balanced", "aggressive") else "balanced", tips)

    def position_advice(
        self,
        phase: str = "mid",
        has_high_ground: bool = False,
        in_open: bool = False,
    ) -> PositionAdvice:
        if phase == "endgame":
            return PositionAdvice("Hraj high ground nebo silný edge box. Nesedej uprostřed bez coveru.", True, "build / high ground", "high" if in_open else "medium")
        if phase == "late":
            return PositionAdvice("Připrav high ground, healy a mobility. Sleduj teamy.", True, "kopec / budova", "medium")
        if in_open:
            return PositionAdvice("Jsi v open – hledej cover nebo build.", False, "budova / skála", "high")
        if has_high_ground:
            return PositionAdvice("Drž high ground, peeka, nenech se under-buildnout.", True, "high ground", "low")
        return PositionAdvice("Hledej elevated pozici nebo pevný cover.", False, "budova / terén", "medium")

    def drop_suggestion(self, style: str = "balanced") -> list[str]:
        return self.DROP_TIPS.get(style, self.DROP_TIPS["balanced"])

    def quick_tip(self, situation: str, hp: int | None = None, shield: int | None = None, **kwargs: Any) -> str:
        situation = situation.lower()
        if situation == "heal":
            return self.heal_advice(hp=hp, shield=shield, **kwargs).message
        if situation == "rotate":
            adv = self.rotation_advice(**kwargs)
            return f"Rotace: {adv.direction}. {adv.tips[0] if adv.tips else adv.reason}"
        if situation == "drop":
            return self.drop_suggestion(kwargs.get("style", "balanced"))[0]
        if situation == "endgame":
            return self.position_advice(phase="endgame", **kwargs).suggestion
        if situation == "fight":
            return "Fight: boxuj při low HP, peeka úhly, po killu heal + third party."
        if situation == "loot":
            return "Loot: zbraň → shield → materials → mobility → healy."
        return "Tip: edge zóny, high ground, heal před rotací."


def get_adapter(game_name: str) -> FortniteAdapter | None:
    name = game_name.lower().replace(" ", "_").replace("-", "_")
    if name in ("fortnite", "fn"):
        return FortniteAdapter()
    return None
