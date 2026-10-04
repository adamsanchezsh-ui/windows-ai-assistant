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
from src.monitoring import MonitoringDashboard
from src.auth import AuthService
from src.game_profiles import GAME_PROFILES


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

    # Register tools with permissions
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
        "priority_monitor": PriorityMonitor(),
    }
    return agent, services


async def interactive_cli(agent: Agent, services: dict) -> None:
    """Simple CLI for testing until full GUI is ready."""
    print("=" * 60)
    print("  Windows AI Assistant  –  CLI režim")
    print("  Příkazy: /quit  /status  /mode <name>  /privacy  /new")
    print("=" * 60)

    services["priority_monitor"].start()

    while True:
        try:
            user = input("\nTy: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user.lower() in ("/quit", "/exit", "q"):
            break
        if user.lower() == "/status":
            import json
            print(json.dumps(agent.status(), indent=2, ensure_ascii=False))
            continue
        if user.lower().startswith("/mode "):
            mode = user.split(maxsplit=1)[1]
            try:
                agent.set_mode(mode)
                print(f"Režim: {agent.mode.value}")
            except ValueError:
                print("Neznámý režim. Dostupné:", [m.value for m in AIMode])
            continue
        if user.lower() == "/privacy":
            agent.settings.privacy_mode = not agent.settings.privacy_mode
            services["screen"].set_privacy(agent.settings.privacy_mode)
            print("Privacy Mode:", "ON" if agent.settings.privacy_mode else "OFF")
            continue
        if user.lower() == "/new":
            conv = agent.new_conversation()
            print("Nová konverzace:", conv.id)
            continue

        try:
            reply = await agent.chat(user)
            print("\nAI:", reply)
            if services["voice"].enabled:
                await services["voice"].speak(reply[:200])
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
