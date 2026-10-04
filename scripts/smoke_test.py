"""
Rychlý smoke test – ověří, že se CYPHERpc načte a základní věci fungují.
Spuštění:  python scripts/smoke_test.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str) -> None:
    print(f" FAIL {msg}")
    raise SystemExit(1)


async def main() -> None:
    print("CYPHERpc smoke test\n")

    from src.settings import get_settings
    s = get_settings()
    s.ensure_dirs()
    ok(f"settings + dirs ({s.data_dir})")

    from src.model import ModelRouter, Message
    router = ModelRouter(s)
    providers = router.list_available()
    ok(f"providers: {providers}")
    if "demo" not in providers:
        fail("demo provider missing")

    resp = await router.chat([Message(role="user", content="ahoj")])
    ok(f"demo chat: {resp.content[:60]}...")

    from src.work.bootstrap import create_work_services
    work = create_work_services(s.data_dir)
    t = work["work_tasks"].add("Smoke test úkol")
    ok(f"task created: {t.id}")
    work["work_tasks"].complete(t.id)
    ok("task completed")

    n = work["work_notes"].add("Test", "smoke note body")
    ok(f"note created: {n.id}")

    from src.voice import VoiceService, list_grok_personas
    v = VoiceService(enabled=False, persona="grok_cs")
    ok(f"voice personas: {len(list_grok_personas())}")
    ok(f"current persona: {v.current_persona().label}")

    from src.game_adapters import FortniteAdapter
    fn = FortniteAdapter()
    tip = fn.heal_advice(hp=40)
    ok(f"fortnite heal: {tip.message[:50]}...")

    from src.core.user_settings import UserSettingsStore
    us = UserSettingsStore(s.data_dir)
    ok(f"user settings loaded (style={us.settings.response.style})")

    print("\nVšechno základní prošlo. Můžeš spustit:")
    print("  python -m src.main")
    print("  python -m src.main --gui")
    if not any([s.openai_api_key, s.xai_api_key, s.anthropic_api_key]):
        print("\nPozn.: běží DEMO režim (bez API klíče). Pro plné AI doplň .env.")


if __name__ == "__main__":
    asyncio.run(main())
