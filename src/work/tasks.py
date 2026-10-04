"""Task / todo manager for work mode."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: str
    title: str
    done: bool = False
    priority: str = "normal"  # low | normal | high | urgent
    due: str | None = None  # ISO date optional
    project: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TaskManager:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "tasks.json"
        self.tasks: dict[str, Task] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for t in data.get("tasks", []):
                self.tasks[t["id"]] = Task(**t)
        except Exception:
            logger.exception("tasks load")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"tasks": [asdict(t) for t in self.tasks.values()]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, title: str, priority: str = "normal", due: str | None = None, project: str = "") -> Task:
        import uuid
        t = Task(id=str(uuid.uuid4())[:8], title=title, priority=priority, due=due, project=project)
        self.tasks[t.id] = t
        self._save()
        return t

    def complete(self, task_id: str) -> bool:
        t = self.tasks.get(task_id)
        if not t:
            return False
        t.done = True
        self._save()
        return True

    def delete(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()
            return True
        return False

    def list_open(self, project: str | None = None) -> list[Task]:
        items = [t for t in self.tasks.values() if not t.done]
        if project:
            items = [t for t in items if t.project == project]
        order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        return sorted(items, key=lambda x: order.get(x.priority, 2))

    def list_all(self) -> list[Task]:
        return list(self.tasks.values())

    def summary_prompt(self) -> str:
        open_tasks = self.list_open()
        if not open_tasks:
            return "Žádné otevřené úkoly."
        lines = [f"- [{t.priority}] {t.title}" + (f" (do {t.due})" if t.due else "") for t in open_tasks]
        return "Pomoz prioritizovat a naplánovat tyto úkoly:\n" + "\n".join(lines)
