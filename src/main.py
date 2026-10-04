"""CYPHERpc entry point."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

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
from src.game_profiles import get_profile
from src.game_adapters import FortniteAdapter
from src.core.memory import MemoryStore
from src.core.personality import Personality
from src.core.model_selector import ModelSelector
from src.core.permissions import PermissionManager
from src.profiles import get_profile as get_user_profile, PROFILES
from src.privacy import PrivacyCenter
from src.notifications import SmartNotifications
from src.ui.control_center import ControlCenter
from src.ui.chat import ChatManager
from src.plugins.base import PluginManager


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_dir / "cypherpc.log", rotation="10 MB", retention="14 days", level="DEBUG")


async def build_agent(settings) -> tuple[Agent, dict]:
    router = ModelRouter(settings)
    memory = MemoryStore(settings.data_dir, enabled=settings.ai.memory_enabled)
    personality = Personality(language=settings.default_language)
    selector = ModelSelector(primary=settings.primary_model)
    perm_mgr = PermissionManager()

    agent = Agent(
        settings, router,
        memory=memory,
        personality=personality,
        model_selector=selector,
        permission_manager=perm_mgr,
    )

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
        wake_word_enabled=False,
    )
    overlay = Overlay(monitor=settings.overlay.monitor, opacity=settings.overlay.opacity)
    performance = PerformanceManager(mode=settings.performance.mode)
    security = SecurityModule(settings.quarantine_dir, use_defender=settings.security.use_defender)
    files = FileManager(confirm_delete=settings.security.confirm_delete)
    clipboard = SmartClipboard()
    browser = BrowserAssistant()
    messaging = MessagingModule()
    auth = AuthService(settings.data_dir, settings.app_secret_key)
    privacy = PrivacyCenter()
    notifications = SmartNotifications()
    control_center = ControlCenter()
    chat_mgr = ChatManager(settings.data_dir)
    plugins = PluginManager()
    fn_adapter = FortniteAdapter()

    # Privacy emergency wiring
    def _privacy_stop() -> None:
        settings.privacy_mode = True
        screen.set_privacy(True)
        voice.set_privacy(True)
        overlay.enabled = False
        agent.enabled = False

    privacy.register_stop_callback(_privacy_stop)

    async def on_voice_command(cmd: str) -> None:
        reply = await agent.chat(cmd)
        await voice.speak(reply[:300])

    voice.set_command_handler(on_voice_command)

    # Fortnite tools
    async def fortnite_heal(hp=None, shield=None, in_combat=False, about_to_rotate=False):
        advice = fn_adapter.heal_advice(hp=hp, shield=shield, in_combat=in_combat, about_to_rotate=about_to_rotate)
        overlay.update(tip=advice.message, status="FORTNITE")
        return {"should_heal": advice.should_heal, "urgency": advice.urgency, "message": advice.message, "items": advice.preferred_items}

    async def fortnite_rotate(zone_closing=False, has_mobility=False, near_fight=False, style="balanced"):
        adv = fn_adapter.rotation_advice(zone_closing=zone_closing, has_mobility=has_mobility, near_fight=near_fight, style=style)
        overlay.update(tip=f"{adv.direction}: {adv.reason}", objective=adv.direction, status="FORTNITE")
        return {"direction": adv.direction, "reason": adv.reason, "priority": adv.priority, "tips": adv.tips}

    async def fortnite_position(phase="mid", has_high_ground=False, in_open=False):
        pos = fn_adapter.position_advice(phase=phase, has_high_ground=has_high_ground, in_open=in_open)
        overlay.update(tip=pos.suggestion, status="FORTNITE")
        return {"suggestion": pos.suggestion, "high_ground": pos.high_ground, "cover": pos.cover, "risk": pos.risk}

    async def fortnite_tip(situation="general", hp=None, shield=None, **kwargs):
        tip = fn_adapter.quick_tip(situation, hp=hp, shield=shield, **kwargs)
        overlay.update(tip=tip, status="FORTNITE")
        if voice.enabled:
            await voice.speak(tip)
        return {"tip": tip}

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
    agent.register_tool("delete_file", lambda path, confirmed=False: asyncio.to_thread(files.delete, Path(path), confirmed), requires_confirmation=True)
    agent.register_tool("performance_stats", lambda: asyncio.to_thread(performance.get_stats))
    agent.register_tool("quarantine_file", lambda path: asyncio.to_thread(security.quarantine_file, Path(path)), requires_confirmation=True)
    agent.register_tool("fortnite_heal", fortnite_heal)
    agent.register_tool("fortnite_rotate", fortnite_rotate)
    agent.register_tool("fortnite_position", fortnite_position)
    agent.register_tool("fortnite_tip", fortnite_tip)

    def on_game_detected(game_name: str, pid: int) -> None:
        profile = get_profile(game_name)
        if profile:
            agent.set_active_game(profile.name, profile.ai_instructions)
            overlay.update(status=profile.display_name.upper())
            logger.info("Game detected: %s (PID %s)", profile.display_name, pid)

    priority_monitor = PriorityMonitor()
    priority_monitor.on_game_detected = on_game_detected

    current_profile_id = "default"

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
        "memory": memory,
        "privacy": privacy,
        "notifications": notifications,
        "control_center": control_center,
        "chat_mgr": chat_mgr,
        "plugins": plugins,
        "current_profile_id": current_profile_id,
    }
    return agent, services


def apply_user_profile(agent: Agent, services: dict, profile_id: str) -> None:
    up = get_user_profile(profile_id)
    services["current_profile_id"] = profile_id
    services["overlay"].enabled = up.overlay
    services["voice"].enabled = up.voice
    services["voice"].hints_enabled = up.voice_hints
    services["voice"].wake_word_enabled = up.wake_word
    services["screen"].vision_mode = up.vision_mode
    services["performance"].set_mode(up.performance_mode)  # type: ignore
    agent.set_style(up.ai_style)
    services["notifications"].set_mode(profile_id)
    if profile_id == "privacy":
        services["privacy"].enable_privacy_mode()
        agent.settings.privacy_mode = True
    else:
        agent.settings.privacy_mode = False
        services["screen"].set_privacy(False)
        services["voice"].set_privacy(False)
        if not agent.enabled:
            agent.enabled = True
    logger.info("Profile applied: %s", up.name)


def show_control_center(agent: Agent, services: dict) -> None:
    stats = services["performance"].get_stats()
    gpu = None
    if stats.get("gpu"):
        gpu = stats["gpu"].get("util")
    status = services["control_center"].build_status(
        ai_online=agent.enabled,
        model=agent.last_model_used or agent.router.current_model_name(),
        mode=agent.mode.value,
        voice=services["voice"].status(),
        vision_mode=services["screen"].vision_mode,
        overlay_on=services["overlay"].enabled,
        game=agent.active_game,
        monitor=agent.settings.selected_monitor,
        cpu=stats.get("cpu_percent", 0),
        ram=stats.get("ram_percent", 0),
        gpu=gpu,
        privacy_mode=agent.settings.privacy_mode,
        profile=services.get("current_profile_id", "default"),
        providers=agent.router.list_available(),
    )
    print(services["control_center"].format_cli(status))


async def interactive_cli(agent: Agent, services: dict) -> None:
    print("=" * 62)
    print("  CYPHERpc v0.2  –  AI Desktop Assistant")
    print("  Wake word: „Cypher“  |  /help pro příkazy")
    print("=" * 62)

    services["priority_monitor"].start()
    fn: FortniteAdapter = services["fn_adapter"]
    overlay = services["overlay"]
    voice = services["voice"]
    memory: MemoryStore = services["memory"]
    privacy: PrivacyCenter = services["privacy"]
    chat_mgr: ChatManager = services["chat_mgr"]

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

        if low in ("/help", "/?"):
            print("""
Příkazy:
  /cc              Control Center (stav)
  /status          JSON status AI
  /mode <name>     normal|reasoning|coding|vision|research|school|gaming|creative
  /profile <id>    gaming|school|privacy|work|default
  /privacy         Privacy Mode ON/OFF
  /stop            Emergency Stop
  /new             Nová konverzace
  /chats           Seznam konverzací
  /memory          Zobraz paměť
  /memory on|off   Zapni/vypni paměť
  /forget all      Smaž paměť
  /style <name>    brief|normal|detailed|technical|simple
  /voice           Voice ON/OFF
  /wake            Wake word ON/OFF
  /fortnite        Fortnite kouč
  /heal [hp] [sh]  Heal rada
  /rotate          Rotace
  /pos [phase]     Pozice
  /what            Co umím?
  /quit /exit       Konec
""")
            continue

        if low in ("/cc", "/control", "/dashboard"):
            show_control_center(agent, services)
            continue

        if low == "/status":
            print(json.dumps(agent.status(), indent=2, ensure_ascii=False))
            continue

        if low.startswith("/mode "):
            try:
                agent.set_mode(user.split(maxsplit=1)[1])
                print(f"Režim: {agent.mode.value}")
            except ValueError:
                print("Dostupné:", [m.value for m in AIMode])
            continue

        if low.startswith("/profile "):
            pid = user.split(maxsplit=1)[1].strip().lower()
            if pid not in PROFILES:
                print("Dostupné profily:", list(PROFILES.keys()))
                continue
            apply_user_profile(agent, services, pid)
            print(f"Profil: {PROFILES[pid].name}")
            show_control_center(agent, services)
            continue

        if low == "/privacy":
            if agent.settings.privacy_mode:
                privacy.disable_privacy_mode()
                agent.settings.privacy_mode = False
                services["screen"].set_privacy(False)
                voice.set_privacy(False)
                agent.enabled = True
                print("Privacy Mode: OFF")
            else:
                privacy.enable_privacy_mode()
                print("Privacy Mode: ON")
            continue

        if low in ("/stop", "/emergency"):
            privacy.emergency_stop()
            print("🚨 EMERGENCY STOP – vše zastaveno")
            continue

        if low == "/new":
            conv = agent.new_conversation()
            chat_mgr.new_conversation()
            print("Nová konverzace:", conv.id)
            continue

        if low == "/chats":
            for c in chat_mgr.list_conversations()[:20]:
                print(f"  {c['id'][:8]}  {c['title'][:40]}  ({c['messages']} msg)")
            continue

        if low == "/memory":
            if not memory.enabled:
                print("Paměť je vypnutá. /memory on")
            else:
                items = memory.list_all()
                if not items:
                    print("(prázdná)")
                for i in items:
                    print(f"  [{i.id}] ({i.category}) {i.content}")
            continue

        if low == "/memory on":
            memory.set_enabled(True)
            print("Paměť zapnuta")
            continue
        if low == "/memory off":
            memory.set_enabled(False)
            print("Paměť vypnuta")
            continue
        if low == "/forget all":
            n = memory.forget_all()
            print(f"Smazáno {n} položek")
            continue

        if low.startswith("/style "):
            agent.set_style(user.split(maxsplit=1)[1])
            print(f"Styl: {agent.personality.style.value}")
            continue

        if low == "/voice":
            print("Voice:", "ON" if voice.toggle() else "OFF")
            continue
        if low == "/wake":
            print("Wake word:", "ON" if voice.toggle_wake_word() else "OFF")
            continue

        if low == "/fortnite":
            profile = get_profile("fortnite")
            if profile:
                agent.set_active_game("fortnite", profile.ai_instructions)
                overlay.enabled = True
                overlay.update(status="FORTNITE", tip="Fortnite kouč aktivní")
                print("Fortnite koučink ON. Ptej se na pozice, heal, rotaci.")
            continue

        if low.startswith("/heal"):
            parts = user.split()
            hp = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            shield = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
            advice = fn.heal_advice(hp=hp, shield=shield)
            print(f"\n🩸 {advice.message}")
            overlay.update(tip=advice.message)
            if voice.enabled:
                await voice.speak(advice.message)
            continue

        if low.startswith("/rotate"):
            adv = fn.rotation_advice()
            print(f"\n📍 {adv.direction} — {adv.reason}")
            for t in adv.tips:
                print(f"   • {t}")
            continue

        if low.startswith("/pos"):
            phase = user.split()[1] if len(user.split()) > 1 else "mid"
            pos = fn.position_advice(phase=phase)
            print(f"\n🏔️  {pos.suggestion}")
            continue

        if low in ("/what", "/what can i do", "/co umis", "/co umíš"):
            print("""
CYPHERpc umí:
  • Běžný chat (jako ChatGPT/Claude) – ptej se na cokoliv
  • Coding, reasoning, research, creative, school
  • Ovládání Windows (okna, soubory, clipboard)
  • Vision / OCR obrazovky
  • Hlas + wake word „Cypher“
  • Herní rady (Fortnite, Minecraft, …)
  • PC monitoring, security, web research
  • Profily: Gaming / School / Privacy / Work
  • Privacy Center + Emergency Stop
Napiš /help pro příkazy, nebo prostě piš česky.
""")
            continue

        # Normal intelligent chat
        try:
            chat_mgr.add_message("user", user)
            reply = await agent.chat(user)
            chat_mgr.add_message("assistant", reply)
            print("\nCYPHERpc:", reply)
            if voice.enabled and voice.hints_enabled:
                await voice.speak(reply[:200])
        except Exception as e:
            logger.exception("Chat error")
            print("Chyba:", e)

    services["priority_monitor"].stop()
    print("CYPHERpc: Nashledanou.")


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_dir)
    logger.info("Starting CYPHERpc v0.2.0")

    async def runner():
        agent, services = await build_agent(settings)
        await interactive_cli(agent, services)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
