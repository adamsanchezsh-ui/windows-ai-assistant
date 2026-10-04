"""Email draft helper – NEVER sends automatically."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EmailDraft:
    id: str
    to: str
    subject: str
    body: str
    cc: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "draft"  # draft | approved | discarded


class EmailDraftService:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "email_drafts.json"
        self.drafts: dict[str, EmailDraft] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for d in data.get("drafts", []):
                self.drafts[d["id"]] = EmailDraft(**d)
        except Exception:
            logger.exception("email drafts load")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"drafts": [asdict(d) for d in self.drafts.values()]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, to: str, subject: str, body: str, cc: str = "") -> EmailDraft:
        import uuid
        d = EmailDraft(id=str(uuid.uuid4())[:8], to=to, subject=subject, body=body, cc=cc)
        self.drafts[d.id] = d
        self._save()
        return d

    def list_drafts(self) -> list[EmailDraft]:
        return [d for d in self.drafts.values() if d.status == "draft"]

    def compose_prompt(self, to: str, intent: str, tone: str = "professional") -> str:
        return (
            f"Napiš draft e-mailu.\n"
            f"Příjemce: {to}\n"
            f"Záměr: {intent}\n"
            f"Tón: {tone}\n"
            f"Vrať: 1) předmět 2) tělo e-mailu. Neodesílej – jen text."
        )

    def improve_prompt(self, draft_body: str) -> str:
        return (
            "Vylepši následující draft e-mailu (jasnost, zdvořilost, struktura). "
            "Zachovej záměr.\n\n" + draft_body
        )
