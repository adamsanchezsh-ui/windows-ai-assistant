"""Local messaging helper – load, summarize, suggest replies (no auto-send)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MessagingModule:
    """Placeholder for local chat / notification integration."""

    def __init__(self):
        self._messages: list[dict[str, Any]] = []

    def load_messages(self, source: str = "local") -> list[dict[str, Any]]:
        return list(self._messages)

    def add_message(self, sender: str, text: str) -> None:
        self._messages.append({"sender": sender, "text": text})

    def summary_prompt(self, messages: list[dict[str, Any]]) -> str:
        body = "\n".join(f"{m['sender']}: {m['text']}" for m in messages[-30:])
        return f"Shrň následující konverzaci:\n\n{body}"

    def reply_prompt(self, messages: list[dict[str, Any]]) -> str:
        body = "\n".join(f"{m['sender']}: {m['text']}" for m in messages[-20:])
        return (
            "Navrhni vhodnou odpověď na základě konverzace. "
            "Neposílej ji automaticky.\n\n" + body
        )
