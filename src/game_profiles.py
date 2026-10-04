"""Game profiles for advisory/training features only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameProfile:
    name: str
    process_names: list[str]
    display_name: str
    ai_instructions: str = ""
    scan_mode: str = "on_demand"
    overlay: bool = True
    voice: bool = False
    performance_mode: str = "performance"
    process_priority: str = "high"
    monitor: int = 1
    extra: dict[str, Any] = field(default_factory=dict)


# Safe advisory profiles only – no cheating, no memory injection, no packet manipulation
GAME_PROFILES: dict[str, GameProfile] = {
    "minecraft": GameProfile(
        name="minecraft",
        process_names=["javaw.exe", "Minecraft.Windows.exe", "minecraft.exe"],
        display_name="Minecraft",
        ai_instructions=(
            "Poskytuj rady pro survival, crafting, farming, redstone a exploration. "
            "Podporuj single-player, private server i development/test. "
            "Nikdy nepodporuj x-ray, killauru nebo jiné cheaty."
        ),
        extra={"modes": ["singleplayer", "private_server", "dev"]},
    ),
    "fortnite": GameProfile(
        name="fortnite",
        process_names=["FortniteClient-Win64-Shipping.exe"],
        display_name="Fortnite",
        ai_instructions="Rady pro building, rotation, loot priority a zone awareness. Pouze poradenské.",
    ),
    "stumble_guys": GameProfile(
        name="stumble_guys",
        process_names=["StumbleGuys.exe"],
        display_name="Stumble Guys",
        ai_instructions="Tipy pro obstácle a timing.",
    ),
    "roblox": GameProfile(
        name="roblox",
        process_names=["RobloxPlayerBeta.exe", "RobloxPlayer.exe"],
        display_name="Roblox",
        ai_instructions="Obecné tipy pro různé experience, bez exploitů.",
    ),
    "gta_v": GameProfile(
        name="gta_v",
        process_names=["GTA5.exe", "GTA5_Enhanced.exe"],
        display_name="GTA V",
        ai_instructions="Mission guidance, map tips, roleplay rady. Žádné mod meny cheaty.",
    ),
    "rocket_league": GameProfile(
        name="rocket_league",
        process_names=["RocketLeague.exe"],
        display_name="Rocket League",
        ai_instructions="Mechanics tips, rotation, kickoff advice.",
    ),
    "cs2": GameProfile(
        name="cs2",
        process_names=["cs2.exe"],
        display_name="Counter-Strike 2",
        ai_instructions="Utility lineups (veřejné), economy, positioning. Žádné wallhack/aimbot rady.",
    ),
    "valorant": GameProfile(
        name="valorant",
        process_names=["VALORANT-Win64-Shipping.exe"],
        display_name="Valorant",
        ai_instructions="Agent tips, lineups, crosshair placement. Pouze legální rady.",
    ),
    "lol": GameProfile(
        name="lol",
        process_names=["League of Legends.exe", "LeagueClient.exe"],
        display_name="League of Legends",
        ai_instructions="Build suggestions, macro, wave management.",
    ),
    "overwatch2": GameProfile(
        name="overwatch2",
        process_names=["Overwatch.exe"],
        display_name="Overwatch 2",
        ai_instructions="Hero tips, team composition, ultimate tracking.",
    ),
    "apex": GameProfile(
        name="apex",
        process_names=["r5apex.exe", "r5apex_dx12.exe"],
        display_name="Apex Legends",
        ai_instructions="Legend tips, rotation, loot priority.",
    ),
    "minecraft_dungeons": GameProfile(
        name="minecraft_dungeons",
        process_names=["Dungeons.exe"],
        display_name="Minecraft Dungeons",
        ai_instructions="Build and artifact advice.",
    ),
    "terraria": GameProfile(
        name="terraria",
        process_names=["Terraria.exe"],
        display_name="Terraria",
        ai_instructions="Boss prep, crafting progression, arena tips.",
    ),
    "ets2": GameProfile(
        name="ets2",
        process_names=["eurotrucks2.exe"],
        display_name="Euro Truck Simulator 2",
        ai_instructions="Route planning, economy tips, truck setup.",
    ),
}


def get_profile(name: str) -> GameProfile | None:
    return GAME_PROFILES.get(name.lower().replace(" ", "_").replace("-", "_"))


def find_profile_by_process(process_name: str) -> GameProfile | None:
    lower = process_name.lower()
    for profile in GAME_PROFILES.values():
        if any(p.lower() == lower for p in profile.process_names):
            return profile
    return None
