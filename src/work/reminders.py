"""Simple reminders / alarms (in-app)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Reminder:
    id: str
    text: str
    when: str  # ISO datetime
    done: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReminderService:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "reminders.json"
        self.items: dict[str, Reminder] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for r in data.get("reminders", []):
                self.items[r["id"]] = Reminder(**r)
        except Exception:
            logger.exception("reminders load")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"reminders": [asdict(r) for r in self.items.values()]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, text: str, when_iso: str) -> Reminder:
        import uuid
        r = Reminder(id=str(uuid.uuid4())[:8], text=text, when=when_iso)
        self.items[r.id] = r
        self._save()
        return r

    def due_now(self) -> list[Reminder]:
        now = datetime.now(timezone.utc)
        out = []
        for r in self.items.values():
            if r.done:
                continue
            try:
                when = datetime.fromisoformat(r.when.replace("Z", "+00:00"))
                if when <= now:
                    out.append(r)
            except Exception:
                continue
        return out

    def list_upcoming(self) -> list[Reminder]:
        items = [r for r in self.items.values() if not r.done]
        return sorted(items, key=lambda x: x.when)

    def complete(self, rid: str) -> bool:
        r = self.items.get(rid)
        if not r:
            return False
        r.done = True
        self._save()
        return True
