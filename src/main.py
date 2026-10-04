"""CYPHERpc entry point – CLI + GUI, full tools, no artificial limits."""

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
from src.tools.web_search import WebAgent
from src.tools.calculator import calculate
from src.tools.api_usage import APIUsageMonitor
from src.tools.diagnostics import health_check, read_logs, system_info
from src.hotkeys import HotkeyManager
from src.command_palette import build_default_palette


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(log_dir / "cypherpc.log", rotation="50 MB", retention="30 days", level="DEBUG")


async def build_agent(settings) -> tuple[Agent, dict]:
    router = ModelRouter(settings)
    memory = MemoryStore(settings.data_dir, enabled=settings.ai.memory_enabled)
    personality = Personality(language=settings.default_language)
    selector = ModelSelector(primary=settings.primary_model)
    perm_mgr = PermissionManager()
    usage = APIUsageMonitor(settings.data_dir, daily_limit=0)  # 0 = unlimited

    agent = Agent(
        settings, router,
        memory=memory,
        personality=personality,
        model_selector=selector,
        permission_manager=perm_mgr,
    )
    # Raise history capacity (no tight limit)
    settings.ai.max_history = max(settings.ai.max_history, 200)

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
    web_agent = WebAgent(max_results=0)  # unlimited results from page

    def _privacy_stop() -> None:
        settings.privacy_mode = True
        screen.set_privacy(True)
        voice.set_privacy(True)
        overlay.enabled = False
        agent.enabled = False

    privacy.register_stop_callback(_privacy_stop)

    async def on_voice_command(cmd: str) -> None:
        reply = await agent.chat(cmd)
        await voice.speak(reply)

    voice.set_command_handler(on_voice_command)

    # --- Tools ---
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

    async def tool_web_search(query: str):
        report = await web_agent.research(query)
        return {"summary": report.summary, "sources": report.sources, "count": len(report.results)}

    async def tool_calculate(expression: str):
        return calculate(expression)

    async def tool_capture_region(left: int, top: int, width: int, height: int):
        path = await asyncio.to_thread(screen.capture_region, left, top, width, height)
        return {"path": str(path)}

    agent.register_tool("list_windows", desktop.list_windows)
    agent.register_tool("focus_window", desktop.focus_window)
    agent.register_tool("type_text", desktop.type_text)
    agent.register_tool("press_key", desktop.press_key)
    agent.register_tool("click", desktop.click)
    agent.register_tool("launch_app", desktop.launch_app, requires_confirmation=True)
    agent.register_tool("capture_screen", lambda monitor=None: asyncio.to_thread(screen.capture, monitor))
    agent.register_tool("capture_region", tool_capture_region)
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
    agent.register_tool("web_search", tool_web_search)
    agent.register_tool("calculate", tool_calculate)

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
        "memory": memory,
        "privacy": privacy,
        "notifications": notifications,
        "control_center": control_center,
        "chat_mgr": chat_mgr,
        "plugins": plugins,
        "web_agent": web_agent,
        "usage": usage,
        "current_profile_id": "default",
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
    services["performance"].set_mode(up.performance_mode)
    agent.set_style(up.ai_style)
    services["notifications"].set_mode(profile_id)
    if profile_id == "privacy":
        services["privacy"].enable_privacy_mode()
        agent.settings.privacy_mode = True
    else:
        agent.settings.privacy_mode = False
        services["screen"].set_privacy(False)
        services["voice"].set_privacy(False)
        agent.enabled = True
    logger.info("Profile: %s", up.name)


def show_control_center(agent: Agent, services: dict) -> None:
    stats = services["performance"].get_stats()
    gpu = stats["gpu"]["util"] if stats.get("gpu") else None
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
    print("API usage:", services["usage"].snapshot())


def status_dict(agent: Agent, services: dict) -> dict:
    stats = services["performance"].get_stats()
    gpu = stats["gpu"]["util"] if stats.get("gpu") else None
    return services["control_center"].build_status(
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


async def interactive_cli(agent: Agent, services: dict) -> None:
    print("=" * 62)
    print("  CYPHERpc v0.3  –  unlimited AI desktop assistant")
    print("  Wake word: Cypher  |  /help  |  python -m src.main --gui")
    print("=" * 62)

    services["priority_monitor"].start()
    fn: FortniteAdapter = services["fn_adapter"]
    overlay = services["overlay"]
    voice = services["voice"]
    memory: MemoryStore = services["memory"]
    privacy: PrivacyCenter = services["privacy"]
    chat_mgr: ChatManager = services["chat_mgr"]
    web: WebAgent = services["web_agent"]

    # Hotkeys
    hk = HotkeyManager()
    hk.register_defaults(
        on_ai_toggle=lambda: print("AI:", "ON" if agent.toggle() else "OFF"),
        on_overlay=lambda: print("Overlay:", "ON" if overlay.toggle() else "OFF"),
        on_voice=lambda: print("Voice:", "ON" if voice.toggle() else "OFF"),
        on_cc=lambda: show_control_center(agent, services),
        on_stop=lambda: (privacy.emergency_stop(), print("EMERGENCY STOP")),
    )

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
/cc /status /mode /profile /privacy /stop /new /chats
/memory [on|off] /forget all /style /voice /wake
/fortnite /heal /rotate /pos
/search <dotaz>     web research se zdroji
/calc <výraz>       kalkulačka
/diag               diagnostika
/logs               poslední log
/usage              API spotřeba (unlimited default)
/what /quit
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
                print("Režim:", agent.mode.value)
            except ValueError:
                print([m.value for m in AIMode])
            continue
        if low.startswith("/profile "):
            pid = user.split(maxsplit=1)[1].strip().lower()
            if pid not in PROFILES:
                print(list(PROFILES.keys()))
                continue
            apply_user_profile(agent, services, pid)
            show_control_center(agent, services)
            continue
        if low == "/privacy":
            if agent.settings.privacy_mode:
                privacy.disable_privacy_mode()
                agent.settings.privacy_mode = False
                services["screen"].set_privacy(False)
                voice.set_privacy(False)
                agent.enabled = True
                print("Privacy: OFF")
            else:
                privacy.enable_privacy_mode()
                print("Privacy: ON")
            continue
        if low in ("/stop", "/emergency"):
            privacy.emergency_stop()
            print("EMERGENCY STOP")
            continue
        if low == "/new":
            print("Nová:", agent.new_conversation().id)
            chat_mgr.new_conversation()
            continue
        if low == "/chats":
            for c in chat_mgr.list_conversations():
                print(f"  {c['id'][:8]}  {c['title']}  ({c['messages']})")
            continue
        if low == "/memory":
            items = memory.list_all() if memory.enabled else []
            print("(vypnuto)" if not memory.enabled else "\n".join(f"[{i.id}] {i.content}" for i in items) or "(prázdná)")
            continue
        if low == "/memory on":
            memory.set_enabled(True); print("Paměť ON"); continue
        if low == "/memory off":
            memory.set_enabled(False); print("Paměť OFF"); continue
        if low == "/forget all":
            print("Smazáno", memory.forget_all()); continue
        if low.startswith("/style "):
            agent.set_style(user.split(maxsplit=1)[1]); print(agent.personality.style.value); continue
        if low == "/voice":
            print("Voice", "ON" if voice.toggle() else "OFF"); continue
        if low == "/wake":
            print("Wake", "ON" if voice.toggle_wake_word() else "OFF"); continue
        if low == "/fortnite":
            p = get_profile("fortnite")
            if p:
                agent.set_active_game("fortnite", p.ai_instructions)
                overlay.enabled = True
                print("Fortnite kouč ON")
            continue
        if low.startswith("/heal"):
            parts = user.split()
            hp = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            sh = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
            a = fn.heal_advice(hp=hp, shield=sh)
            print(a.message); overlay.update(tip=a.message)
            continue
        if low.startswith("/rotate"):
            a = fn.rotation_advice()
            print(a.direction, "—", a.reason)
            for t in a.tips: print(" •", t)
            continue
        if low.startswith("/pos"):
            phase = user.split()[1] if len(user.split()) > 1 else "mid"
            print(fn.position_advice(phase=phase).suggestion); continue
        if low.startswith("/search "):
            q = user.split(maxsplit=1)[1]
            report = await web.research(q)
            print(report.summary)
            print("Zdroje:", report.sources)
            # Also ask AI to synthesize
            prompt = web.research_prompt(report)
            reply = await agent.chat(prompt)
            print("\nCYPHERpc:", reply)
            continue
        if low.startswith("/calc "):
            print(calculate(user.split(maxsplit=1)[1])); continue
        if low == "/diag":
            print(json.dumps(health_check(agent.router.list_available(), agent.settings.data_dir), indent=2))
            print(system_info()); continue
        if low == "/logs":
            print(read_logs(agent.settings.log_dir)); continue
        if low == "/usage":
            print(services["usage"].snapshot()); continue
        if low in ("/what", "/co umíš", "/co umis"):
            print("Chat, coding, vision, web, Windows, gaming, hlas Cypher, privacy, GUI — piš cokoliv.")
            continue

        try:
            chat_mgr.add_message("user", user)
            reply = await agent.chat(user)
            chat_mgr.add_message("assistant", reply)
            # Track usage if response has usage info (best-effort)
            print("\nCYPHERpc:", reply)
            if voice.enabled and voice.hints_enabled:
                await voice.speak(reply)
        except Exception as e:
            logger.exception("chat")
            print("Chyba:", e)

    hk.unbind_all()
    services["priority_monitor"].stop()
    print("CYPHERpc: Nashledanou.")


def run_gui(agent: Agent, services: dict) -> None:
    try:
        from src.ui.gui import CypherGUI
    except Exception as e:
        print("GUI nedostupné:", e)
        print("Nainstaluj: pip install customtkinter")
        return

    services["priority_monitor"].start()

    async def on_send(text: str) -> str:
        services["chat_mgr"].add_message("user", text)
        reply = await agent.chat(text)
        services["chat_mgr"].add_message("assistant", reply)
        return reply

    gui = CypherGUI(
        on_send=on_send,
        get_status=lambda: status_dict(agent, services),
        on_privacy=lambda: services["privacy"].enable_privacy_mode(),
        on_stop=lambda: services["privacy"].emergency_stop(),
    )
    try:
        gui.run()
    finally:
        services["priority_monitor"].stop()


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_dir)
    logger.info("Starting CYPHERpc v0.3.0")

    use_gui = "--gui" in sys.argv or "-g" in sys.argv

    async def runner():
        agent, services = await build_agent(settings)
        if use_gui:
            # GUI blocks; run setup then hand off
            return agent, services
        await interactive_cli(agent, services)
        return None, None

    if use_gui:
        agent, services = asyncio.run(runner())
        if agent:
            run_gui(agent, services)
    else:
        asyncio.run(runner())


if __name__ == "__main__":
    main()
