"""Entry point for Windows AI Assistant."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loguru import logger

from src.settings import get_settings
from src.model import ModelRouter
from src.agent import Agent, AIMode
from src.desktop import DesktopController
from src.screen import ScreenService
from src.voice import VoiceService
from src.overlay import Overlay
from src.priority_monitor import PriorityMonitor
from src.performance import PerformanceManager
from src.security import SecurityModule
from src.files import FileManager
from src.clipboard import SmartClipboard
from src.browser import BrowserAssistant
from src.messaging import MessagingModule
from src.auth import AuthService
from src.game_profiles import GAME_PROFILES, get_profile
from src.game_adapters import FortniteAdapter, get_adapter


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_dir / "assistant.log", rotation="10 MB", retention="14 days", level="DEBUG")


async def build_agent(settings) -> tuple[Agent, dict]:
    router = ModelRouter(settings)
    agent = Agent(settings, router)

    desktop = DesktopController()
    screen = ScreenService(
        settings.data_dir,
        vision_mode=settings.ai.vision_mode,
        selected_monitor=settings.selected_monitor,
        privacy_mode=settings.privacy_mode,
    )
    voice = VoiceService(
        language=settings.voice.language,
        volume=settings.voice.volume,
        rate=settings.voice.rate,
        enabled=settings.voice.enabled,
    )
    overlay = Overlay(monitor=settings.overlay.monitor, opacity=settings.overlay.opacity)
    performance = PerformanceManager(mode=settings.performance.mode)
    security = SecurityModule(settings.quarantine_dir, use_defender=settings.security.use_defender)
    files = FileManager(confirm_delete=settings.security.confirm_delete)
    clipboard = SmartClipboard()
    browser = BrowserAssistant()
    messaging = MessagingModule()
    auth = AuthService(settings.data_dir, settings.app_secret_key)

    # --- Fortnite coaching adapter ---
    fn_adapter = FortniteAdapter()

    async def fortnite_heal(hp: int | None = None, shield: int | None = None,
                            in_combat: bool = False, about_to_rotate: bool = False):
        advice = fn_adapter.heal_advice(
            hp=hp, shield=shield, in_combat=in_combat, about_to_rotate=about_to_rotate
        )
        overlay.update(tip=advice.message, status="FORTNITE")
        return {
            "should_heal": advice.should_heal,
            "urgency": advice.urgency,
            "message": advice.message,
            "items": advice.preferred_items,
        }

    async def fortnite_rotate(zone_closing: bool = False, has_mobility: bool = False,
                              near_fight: bool = False, style: str = "balanced"):
        adv = fn_adapter.rotation_advice(
            zone_closing=zone_closing,
            has_mobility=has_mobility,
            near_fight=near_fight,
            style=style,
        )
        tip = f"{adv.direction}: {adv.reason}"
        overlay.update(tip=tip, objective=adv.direction, status="FORTNITE")
        return {
            "direction": adv.direction,
            "reason": adv.reason,
            "priority": adv.priority,
            "tips": adv.tips,
        }

    async def fortnite_position(phase: str = "mid", has_high_ground: bool = False,
                                in_open: bool = False):
        pos = fn_adapter.position_advice(
            phase=phase, has_high_ground=has_high_ground, in_open=in_open
        )
        overlay.update(tip=pos.suggestion, status="FORTNITE")
        return {
            "suggestion": pos.suggestion,
            "high_ground": pos.high_ground,
            "cover": pos.cover,
            "risk": pos.risk,
        }

    async def fortnite_tip(situation: str = "general", hp: int | None = None,
                           shield: int | None = None, **kwargs):
        tip = fn_adapter.quick_tip(situation, hp=hp, shield=shield, **kwargs)
        overlay.update(tip=tip, status="FORTNITE")
        if voice.enabled:
            await voice.speak(tip)
        return {"tip": tip}

    async def fortnite_status(hp: int | None = None, shield: int | None = None,
                              phase: str = "mid", zone_closing: bool = False,
                              in_combat: bool = False, style: str = "balanced"):
        result = fn_adapter.full_status_advice(
            hp=hp, shield=shield, phase=phase,
            zone_closing=zone_closing, in_combat=in_combat, style=style,
        )
        overlay.update(tip=result["overlay_line"], status="FORTNITE")
        return result

    # Register tools
    agent.register_tool("list_windows", desktop.list_windows)
    agent.register_tool("focus_window", desktop.focus_window)
    agent.register_tool("type_text", desktop.type_text)
    agent.register_tool("press_key", desktop.press_key)
    agent.register_tool("click", desktop.click)
    agent.register_tool("launch_app", desktop.launch_app, requires_confirmation=True)

    agent.register_tool("capture_screen", lambda monitor=None: asyncio.to_thread(screen.capture, monitor))
    agent.register_tool("ocr_screen", lambda: asyncio.to_thread(screen.ocr))

    agent.register_tool("get_clipboard", lambda: asyncio.to_thread(clipboard.get))
    agent.register_tool("set_clipboard", lambda text: asyncio.to_thread(clipboard.set, text))

    agent.register_tool("search_files", lambda root, pattern: asyncio.to_thread(files.search, Path(root), pattern))
    agent.register_tool(
        "delete_file",
        lambda path, confirmed=False: asyncio.to_thread(files.delete, Path(path), confirmed),
        requires_confirmation=True,
    )

    agent.register_tool("performance_stats", lambda: asyncio.to_thread(performance.get_stats))
    agent.register_tool(
        "quarantine_file",
        lambda path: asyncio.to_thread(security.quarantine_file, Path(path)),
        requires_confirmation=True,
    )

    # Fortnite tools
    agent.register_tool("fortnite_heal", fortnite_heal)
    agent.register_tool("fortnite_rotate", fortnite_rotate)
    agent.register_tool("fortnite_position", fortnite_position)
    agent.register_tool("fortnite_tip", fortnite_tip)
    agent.register_tool("fortnite_status", fortnite_status)

    def on_game_detected(game_name: str, pid: int) -> None:
        profile = get_profile(game_name)
        if profile:
            agent.set_active_game(profile.name, profile.ai_instructions)
            overlay.update(status=profile.display_name.upper())
            logger.info("Game detected: %s (PID %s)", profile.display_name, pid)

    priority_monitor = PriorityMonitor()
    priority_monitor.on_game_detected = on_game_detected

    services = {
        "desktop": desktop,
        "screen": screen,
        "voice": voice,
        "overlay": overlay,
        "performance": performance,
        "security": security,
        "files": files,
        "clipboard": clipboard,
        "browser": browser,
        "messaging": messaging,
        "auth": auth,
        "priority_monitor": priority_monitor,
        "fn_adapter": fn_adapter,
    }
    return agent, services


async def interactive_cli(agent: Agent, services: dict) -> None:
    """Simple CLI for testing until full GUI is ready."""
    print("=" * 60)
    print("  Windows AI Assistant  –  CLI režim")
    print("  Příkazy:")
    print("    /quit  /status  /mode <name>  /privacy  /new")
    print("    /fortnite          – aktivuj Fortnite koučink")
    print("    /heal [hp] [shield] – kdy popnout heal")
    print("    /rotate            – kam jít / rotace")
    print("    /pos [early|mid|late|endgame] – dobrá pozice")
    print("=" * 60)

    services["priority_monitor"].start()
    fn: FortniteAdapter = services["fn_adapter"]
    overlay = services["overlay"]
    voice = services["voice"]

    while True:
        try:
            user = input("\nTy: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue

        low = user.lower()

        if low in ("/quit", "/exit", "q"):
            break

        if low == "/status":
            import json
            print(json.dumps(agent.status(), indent=2, ensure_ascii=False))
            continue

        if low.startswith("/mode "):
            mode = user.split(maxsplit=1)[1]
            try:
                agent.set_mode(mode)
                print(f"Režim: {agent.mode.value}")
            except ValueError:
                print("Neznámý režim. Dostupné:", [m.value for m in AIMode])
            continue

        if low == "/privacy":
            agent.settings.privacy_mode = not agent.settings.privacy_mode
            services["screen"].set_privacy(agent.settings.privacy_mode)
            print("Privacy Mode:", "ON" if agent.settings.privacy_mode else "OFF")
            continue

        if low == "/new":
            conv = agent.new_conversation()
            print("Nová konverzace:", conv.id)
            continue

        # --- Fortnite shortcuts ---
        if low == "/fortnite":
            profile = get_profile("fortnite")
            if profile:
                agent.set_active_game("fortnite", profile.ai_instructions)
                overlay.enabled = True
                overlay.update(status="FORTNITE", tip="Fortnite kouč aktivní")
                print("Fortnite koučink ZAPNUTÝ. Ptej se na pozice, heal, rotaci...")
                print("Příklady: 'kam mám dropnout?', 'mám 40 HP, healnout?', 'kam rotovat?'")
            continue

        if low.startswith("/heal"):
            parts = user.split()
            hp = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            shield = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
            advice = fn.heal_advice(hp=hp, shield=shield)
            print(f"\n🩸 {advice.message}")
            print(f"   Urgence: {advice.urgency} | Doporučené: {', '.join(advice.preferred_items[:3])}")
            overlay.update(tip=advice.message)
            if voice.enabled:
                await voice.speak(advice.message)
            continue

        if low.startswith("/rotate"):
            adv = fn.rotation_advice()
            print(f"\n📍 Rotace: {adv.direction}")
            print(f"   Důvod: {adv.reason}")
            for t in adv.tips:
                print(f"   • {t}")
            overlay.update(tip=f"{adv.direction} — {adv.reason}", objective=adv.direction)
            continue

        if low.startswith("/pos"):
            parts = user.split()
            phase = parts[1] if len(parts) > 1 else "mid"
            pos = fn.position_advice(phase=phase)
            print(f"\n🏔️  {pos.suggestion}")
            print(f"   Cover: {pos.cover} | Riziko: {pos.risk}")
            overlay.update(tip=pos.suggestion)
            continue

        # Normal chat
        try:
            reply = await agent.chat(user)
            print("\nAI:", reply)
            if voice.enabled:
                await voice.speak(reply[:200])
        except Exception as e:
            logger.exception("Chat error")
            print("Chyba:", e)

    services["priority_monitor"].stop()
    print("Nashledanou.")


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_dir)
    logger.info("Starting Windows AI Assistant v0.1.0")

    async def runner():
        agent, services = await build_agent(settings)
        await interactive_cli(agent, services)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
