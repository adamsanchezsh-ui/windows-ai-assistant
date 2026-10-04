"""Chat conversation manager – multi-conversation, history, export."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    role: str  # user | assistant | system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    attachments: list[str] = field(default_factory=list)


@dataclass
class ChatThread:
    id: str
    title: str = "Nová konverzace"
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatManager:
    """
    Moderní chat: více konverzací, historie, hledání, přílohy,
    regenerace, stop, kopírování, export.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir / "chats"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.threads: dict[str, ChatThread] = {}
        self.active_id: str | None = None
        self._generating = False
        self._load_index()

    def _load_index(self) -> None:
        index = self.data_dir / "index.json"
        if index.exists():
            try:
                data = json.loads(index.read_text(encoding="utf-8"))
                for tid in data.get("ids", []):
                    self._load_thread(tid)
            except Exception:
                logger.exception("Chat index load failed")

    def _save_index(self) -> None:
        index = self.data_dir / "index.json"
        index.write_text(
            json.dumps({"ids": list(self.threads.keys())}, indent=2),
            encoding="utf-8",
        )

    def _load_thread(self, tid: str) -> None:
        path = self.data_dir / f"{tid}.json"
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        msgs = [ChatMessage(**m) for m in data.get("messages", [])]
        self.threads[tid] = ChatThread(
            id=data["id"],
            title=data.get("title", "Nová konverzace"),
            messages=msgs,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def _persist(self, thread: ChatThread) -> None:
        path = self.data_dir / f"{thread.id}.json"
        path.write_text(
            json.dumps({
                "id": thread.id,
                "title": thread.title,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "messages": [asdict(m) for m in thread.messages],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._save_index()

    def new_conversation(self, title: str = "Nová konverzace") -> ChatThread:
        import uuid
        tid = str(uuid.uuid4())[:12]
        thread = ChatThread(id=tid, title=title)
        self.threads[tid] = thread
        self.active_id = tid
        self._persist(thread)
        return thread

    def get_active(self) -> ChatThread | None:
        if self.active_id:
            return self.threads.get(self.active_id)
        return None

    def switch(self, tid: str) -> ChatThread | None:
        if tid in self.threads:
            self.active_id = tid
            return self.threads[tid]
        return None

    def delete(self, tid: str) -> bool:
        if tid not in self.threads:
            return False
        del self.threads[tid]
        path = self.data_dir / f"{tid}.json"
        if path.exists():
            path.unlink()
        if self.active_id == tid:
            self.active_id = next(iter(self.threads), None)
        self._save_index()
        return True

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        results = []
        for t in self.threads.values():
            if q in t.title.lower() or any(q in m.content.lower() for m in t.messages):
                results.append({"id": t.id, "title": t.title, "updated_at": t.updated_at})
        return results

    def add_message(self, role: str, content: str, attachments: list[str] | None = None) -> None:
        thread = self.get_active()
        if not thread:
            thread = self.new_conversation()
        thread.messages.append(ChatMessage(role=role, content=content, attachments=attachments or []))
        thread.updated_at = datetime.now(timezone.utc).isoformat()
        if len(thread.messages) <= 2 and thread.title == "Nová konverzace" and role == "user":
            thread.title = content[:60] + ("…" if len(content) > 60 else "")
        self._persist(thread)

    def export(self, tid: str | None = None, fmt: str = "md") -> str:
        thread = self.threads.get(tid) if tid else self.get_active()
        if not thread:
            return ""
        if fmt == "json":
            return json.dumps({
                "id": thread.id,
                "title": thread.title,
                "messages": [asdict(m) for m in thread.messages],
            }, ensure_ascii=False, indent=2)
        lines = [f"# {thread.title}\n"]
        for m in thread.messages:
            lines.append(f"**{m.role}**: {m.content}\n")
        return "\n".join(lines)

    def list_conversations(self) -> list[dict[str, Any]]:
        return [
            {"id": t.id, "title": t.title, "updated_at": t.updated_at, "messages": len(t.messages)}
            for t in sorted(self.threads.values(), key=lambda x: x.updated_at, reverse=True)
        ]

    @property
    def is_generating(self) -> bool:
        return self._generating

    def stop_generation(self) -> None:
        self._generating = False
