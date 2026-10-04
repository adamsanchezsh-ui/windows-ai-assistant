"""Optional long-term memory with user control."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    id: str
    content: str
    category: str = "general"  # general | preference | fact | project
    created_at: str = ""
    source: str = "user"  # user | auto

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """
    Volitelná dlouhodobá paměť.
    Uživatel může: zapnout/vypnout, prohlížet, smazat položku, smazat vše.
    Citlivé věci se neukládají automaticky bez explicitního souhlasu.
    """

    def __init__(self, data_dir: Path, enabled: bool = False):
        self.path = data_dir / "memory.json"
        self.enabled = enabled
        self._items: dict[str, MemoryItem] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            for item in raw.get("items", []):
                mi = MemoryItem(**item)
                self._items[mi.id] = mi
        except Exception:
            logger.exception("Failed to load memory")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"items": [asdict(i) for i in self._items.values()]}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def add(self, content: str, category: str = "general", source: str = "user") -> MemoryItem:
        if not self.enabled and source == "auto":
            raise RuntimeError("Memory is disabled")
        import uuid
        item = MemoryItem(id=str(uuid.uuid4())[:8], content=content, category=category, source=source)
        self._items[item.id] = item
        self._save()
        return item

    def list_all(self) -> list[MemoryItem]:
        return list(self._items.values())

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def forget(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            self._save()
            return True
        return False

    def forget_all(self) -> int:
        n = len(self._items)
        self._items.clear()
        self._save()
        return n

    def as_context(self, limit: int = 20) -> str:
        if not self.enabled or not self._items:
            return ""
        lines = [f"- [{i.category}] {i.content}" for i in list(self._items.values())[:limit]]
        return "Uložené informace o uživateli:\n" + "\n".join(lines)
