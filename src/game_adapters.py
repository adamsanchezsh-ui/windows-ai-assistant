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
    urgency: str  # none | low | medium | high | critical
    message: str
    preferred_items: list[str]


@dataclass
class RotationAdvice:
    direction: str
    reason: str
    priority: str  # safe | balanced | aggressive
    tips: list[str]


@dataclass
class PositionAdvice:
    suggestion: str
    high_ground: bool
    cover: str
    risk: str


class FortniteAdapter:
    """
    Poradenský adaptér pro Fortnite.
    Používá pouze to, co uživatel / vision / OCR poskytne –
    žádné čtení paměti hry, žádný ESP, žádný aimbot.
    """

    # Typické drop tipy (obecné, bez závislosti na aktuální mapě)
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
            "Vyhûej se early fightům, hraj o placement.",
        ],
    }

    HEAL_PRIORITY = [
        "Chug Splash",
        "Shield Potion",
        "Big Shield Potion",
        "Medkit",
        "Bandages",
        "Fish / Food",
    ]

    def __init__(self, profile: GameProfile | None = None):
        self.profile = profile or get_profile("fortnite")
        thresholds = (self.profile.extra or {}).get("heal_thresholds", {})
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
        """
        Kdy popnout heal / shield.
        Hodnoty hp/shield může dodat vision/OCR nebo uživatel.
        """
        if hp is None and shield is None:
            return HealAdvice(
                should_heal=False,
                urgency="none",
                message="Nevím aktuální HP/shield – řekni mi stav nebo zapni vision.",
                preferred_items=self.HEAL_PRIORITY,
            )

        hp = hp if hp is not None else 100
        shield = shield if shield is not None else 0

        if not has_heals:
            return HealAdvice(
                False, "none",
                "Nemáš healy – hledej loot (Shield Pot, Medkit, Bandage).",
                self.HEAL_PRIORITY,
            )

        if in_combat and hp > self.critical_hp:
            return HealAdvice(
                False, "low",
                "Jsi ve fightu – heal až po něm (nebo do boxu).",
                self.HEAL_PRIORITY,
            )

        if hp <= self.critical_hp:
            return HealAdvice(
                True, "critical",
                f"KRITICKÉ HP ({hp})! Okamžitě heal (Medkit / Bandage), schovej se.",
                ["Medkit", "Bandages", "Chug Splash"],
            )

        if hp <= self.low_hp:
            return HealAdvice(
                True, "high",
                f"Nízké HP ({hp}) – heal co nejdřív, až budeš v bezpečí.",
                ["Medkit", "Bandages", "Chug Splash"],
            )

        if about_to_rotate and shield < self.pre_rotate_min_shield:
            return HealAdvice(
                True, "medium",
                f"Před rotací doplň shield (máš {shield}). Ideálně 50+.",
                ["Shield Potion", "Chug Splash", "Big Shield Potion"],
            )

        if shield < self.low_shield and not in_combat:
            return HealAdvice(
                True, "medium",
                f"Nízký shield ({shield}) – popni Shield Pot, než půjdeš dál.",
                ["Shield Potion", "Chug Splash"],
            )

        return HealAdvice(
            False, "none",
            f"HP/shield OK ({hp}/{shield}). Šetři healy na fight / endgame.",
            self.HEAL_PRIORITY,
        )

    def rotation_advice(
        self,
        zone_closing: bool = False,
        has_mobility: bool = False,
        near_fight: bool = False,
        materials: int | None = None,
        style: str = "balanced",
    ) -> RotationAdvice:
        """Kam jít dál – obecné principy bez map hacků."""
        tips: list[str] = []

        if zone_closing:
            tips.append("Storm se zavírá – prioritizuj cestu do zóny.")
            if has_mobility:
                tips.append("Použij Shockwave / Grappler / vozidlo na rychlou rotaci.")
            else:
                tips.append("Běž edge zóny, drž cover, ne open field.")
            return RotationAdvice(
                direction="do zóny (edge)",
                reason="Storm pressure",
                priority="safe",
                tips=tips,
            )

        if near_fight:
            tips.append("Blízký fight – zvaž third-party z výhodné pozice.")
            tips.append("Nebo se stáhni a hraj o placement.")
            return RotationAdvice(
                direction="k fightu (opatrně) nebo pryč",
                reason="Third-party příležitost / riziko",
                priority="aggressive" if style == "aggressive" else "balanced",
                tips=tips,
            )

        tips.append("Rotuj směrem k předpokládané další zóně.")
        tips.append("Preferuj high ground a přirozený cover.")
        tips.append("Vyhni se dlouhému běhu přes otevřené pole.")
        if materials is not None and materials < 100:
            tips.append(f"Málo materials ({materials}) – cestou farmi stromy/zdi.")

        return RotationAdvice(
            direction="edge zóny / high ground",
            reason="Bezpečná mid-game rotace",
            priority=style if style in ("safe", "balanced", "aggressive") else "balanced",
            tips=tips,
        )

    def position_advice(
        self,
        phase: str = "mid",  # early | mid | late | endgame
        has_high_ground: bool = False,
        in_open: bool = False,
    ) -> PositionAdvice:
        if phase == "endgame":
            return PositionAdvice(
                suggestion="Hraj high ground nebo silný edge box. Nesedej uprostřed zóny bez coveru.",
                high_ground=True,
                cover="vlastní build / přírodní high ground",
                risk="high" if in_open else "medium",
            )
        if phase == "late":
            return PositionAdvice(
                suggestion="Připrav si high ground setup, mít healy a mobility. Sleduj okolní teamy.",
                high_ground=True,
                cover="kopec / budova / vlastní rampa",
                risk="medium",
            )
        if in_open:
            return PositionAdvice(
                suggestion="Jsi v open – okamžitě hledej cover (budova, skála, strom) nebo build.",
                high_ground=False,
                cover="nejbližší přírodní / build",
                risk="high",
            )
        if has_high_ground:
            return PositionAdvice(
                suggestion="Máš high ground – drž ho, info peeka, nenech se under-buildnout.",
                high_ground=True,
                cover="high ground",
                risk="low",
            )
        return PositionAdvice(
            suggestion="Hledej elevated pozici nebo pevný cover. Připrav únikovou cestu.",
            high_ground=False,
            cover="budova / terén",
            risk="medium",
        )

    def drop_suggestion(self, style: str = "balanced") -> list[str]:
        return self.DROP_TIPS.get(style, self.DROP_TIPS["balanced"])

    def quick_tip(
        self,
        situation: str,
        hp: int | None = None,
        shield: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Krátká rada pro overlay / voice.
        situation: drop | rotate | heal | fight | endgame | loot | general
        """
        situation = situation.lower()

        if situation == "heal":
            advice = self.heal_advice(hp=hp, shield=shield, **kwargs)
            return advice.message

        if situation == "rotate":
            adv = self.rotation_advice(**kwargs)
            return f"Rotace: {adv.direction}. {adv.tips[0] if adv.tips else adv.reason}"

        if situation == "drop":
            tips = self.drop_suggestion(kwargs.get("style", "balanced"))
            return tips[0]

        if situation == "endgame":
            pos = self.position_advice(phase="endgame", **kwargs)
            return pos.suggestion

        if situation == "fight":
            return (
                "Fight: boxuj se při low HP, peeka úhly, "
                "po killu okamžitě heal + check third party."
            )

        if situation == "loot":
            return (
                "Loot priorita: zbraň → shield → materials → mobility → healy. "
                "Netrav čas over-lootem."
            )

        return (
            "Fortnite tip: drž edge zóny, high ground, "
            "heal před rotací, pozor na third party."
        )

    def full_status_advice(
        self,
        hp: int | None = None,
        shield: int | None = None,
        phase: str = "mid",
        zone_closing: bool = False,
        in_combat: bool = False,
        style: str = "balanced",
    ) -> dict[str, Any]:
        """Komplexní rada pro agent / overlay."""
        heal = self.heal_advice(
            hp=hp,
            shield=shield,
            in_combat=in_combat,
            about_to_rotate=zone_closing,
        )
        rotation = self.rotation_advice(
            zone_closing=zone_closing,
            style=style,
        )
        position = self.position_advice(phase=phase)

        summary_parts = []
        if heal.should_heal:
            summary_parts.append(heal.message)
        summary_parts.append(f"Pozice: {position.suggestion}")
        summary_parts.append(f"Rotace: {rotation.direction} — {rotation.reason}")

        return {
            "summary": " | ".join(summary_parts),
            "heal": heal,
            "rotation": rotation,
            "position": position,
            "overlay_line": heal.message if heal.urgency in ("critical", "high") else position.suggestion,
        }


def get_adapter(game_name: str) -> FortniteAdapter | None:
    """Factory – zatím Fortnite, později další hry."""
    name = game_name.lower().replace(" ", "_").replace("-", "_")
    if name in ("fortnite", "fn"):
        return FortniteAdapter()
    return None
