"""Smart Notifications – summary, priority, DND, mode-aware."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class NotifPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    id: str
    title: str
    body: str
    source: str = "system"
    priority: NotifPriority = NotifPriority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read: bool = False


class SmartNotifications:
    def __init__(self) -> None:
        self._items: list[Notification] = []
        self.dnd = False
        self.mode: str = "default"  # default | gaming | school | work

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        if mode == "gaming":
            self.dnd = True
        elif mode == "school":
            self.dnd = False

    def add(self, title: str, body: str, source: str = "system",
            priority: NotifPriority = NotifPriority.NORMAL) -> Notification | None:
        if self.dnd and priority not in (NotifPriority.URGENT, NotifPriority.HIGH):
            logger.debug("DND: suppressed %s", title)
            return None
        import uuid
        n = Notification(
            id=str(uuid.uuid4())[:8],
            title=title,
            body=body,
            source=source,
            priority=priority,
        )
        self._items.append(n)
        return n

    def list_unread(self) -> list[Notification]:
        return [n for n in self._items if not n.read]

    def mark_read(self, notif_id: str) -> None:
        for n in self._items:
            if n.id == notif_id:
                n.read = True

    def summary_prompt(self) -> str:
        unread = self.list_unread()[-15:]
        if not unread:
            return "Žádné nové notifikace."
        lines = [f"[{n.priority.value}] {n.source}: {n.title} — {n.body}" for n in unread]
        return "Shrň tyto notifikace podle priority:\n" + "\n".join(lines)
