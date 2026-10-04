"""
Messaging module – load/display messages, AI summary, suggested replies.
NEVER auto-sends without user confirmation.
"""

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
    id: str
    thread_id: str
    sender: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    direction: str = "in"  # in | out
    read: bool = False


@dataclass
class Thread:
    id: str
    title: str
    participants: list[str] = field(default_factory=list)
    platform: str = "local"  # local | discord | slack | email | sms
    messages: list[ChatMessage] = field(default_factory=list)


class MessagingService:
    """
    Lokální messaging + návrhy odpovědí.
    Integrace s Discord/Slack/e-mailem = později přes pluginy;
    jádro umí pracovat s libovolnými načtenými zprávami.
    """

    def __init__(self, data_dir: Path):
        self.path = data_dir / "messages.json"
        self.threads: dict[str, Thread] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for t in data.get("threads", []):
                msgs = [ChatMessage(**m) for m in t.get("messages", [])]
                self.threads[t["id"]] = Thread(
                    id=t["id"],
                    title=t.get("title", ""),
                    participants=t.get("participants", []),
                    platform=t.get("platform", "local"),
                    messages=msgs,
                )
        except Exception:
            logger.exception("messages load")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "threads": [
                {
                    "id": t.id,
                    "title": t.title,
                    "participants": t.participants,
                    "platform": t.platform,
                    "messages": [asdict(m) for m in t.messages],
                }
                for t in self.threads.values()
            ]
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_thread(self, title: str, participants: list[str] | None = None, platform: str = "local") -> Thread:
        import uuid
        tid = str(uuid.uuid4())[:10]
        t = Thread(id=tid, title=title, participants=participants or [], platform=platform)
        self.threads[tid] = t
        self._save()
        return t

    def add_message(self, thread_id: str, sender: str, text: str, direction: str = "in") -> ChatMessage:
        import uuid
        t = self.threads.get(thread_id)
        if not t:
            t = self.create_thread(title=sender or "Chat")
            thread_id = t.id
        msg = ChatMessage(
            id=str(uuid.uuid4())[:8],
            thread_id=thread_id,
            sender=sender,
            text=text,
            direction=direction,
        )
        t.messages.append(msg)
        self._save()
        return msg

    def list_threads(self) -> list[dict[str, Any]]:
        out = []
        for t in self.threads.values():
            last = t.messages[-1].text[:80] if t.messages else ""
            out.append({
                "id": t.id,
                "title": t.title,
                "platform": t.platform,
                "messages": len(t.messages),
                "last": last,
            })
        return out

    def get_messages(self, thread_id: str, limit: int = 0) -> list[ChatMessage]:
        t = self.threads.get(thread_id)
        if not t:
            return []
        msgs = t.messages
        if limit and limit > 0:
            return msgs[-limit:]
        return list(msgs)  # no artificial limit when limit=0

    def summary_prompt(self, thread_id: str) -> str:
        msgs = self.get_messages(thread_id)
        body = "\n".join(f"{m.sender}: {m.text}" for m in msgs)
        return f"Shrň následující konverzaci stručně a vypiš akční body:\n\n{body}"

    def reply_prompt(self, thread_id: str, tone: str = "professional") -> str:
        msgs = self.get_messages(thread_id)
        body = "\n".join(f"{m.sender}: {m.text}" for m in msgs[-30:])
        return (
            f"Navrhni vhodnou odpověď (tón: {tone}). "
            f"NEODESÍLEJ ji – jen text návrhu pro uživatele ke schválení.\n\n{body}"
        )

    def draft_reply(self, thread_id: str, text: str) -> dict[str, Any]:
        """Uloží návrh odpovědi – odeslání vyžaduje explicitní potvrzení."""
        return {
            "status": "draft",
            "thread_id": thread_id,
            "text": text,
            "note": "Zpráva NENÍ odeslána. Potvrď ručně / přes plugin.",
        }
