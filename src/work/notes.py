"""Notes + meeting notes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Note:
    id: str
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    kind: str = "note"  # note | meeting | idea
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class NotesService:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "notes.json"
        self.notes: dict[str, Note] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for n in data.get("notes", []):
                self.notes[n["id"]] = Note(**n)
        except Exception:
            logger.exception("notes load")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"notes": [asdict(n) for n in self.notes.values()]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, title: str, body: str, tags: list[str] | None = None, kind: str = "note") -> Note:
        import uuid
        n = Note(id=str(uuid.uuid4())[:8], title=title, body=body, tags=tags or [], kind=kind)
        self.notes[n.id] = n
        self._save()
        return n

    def update(self, note_id: str, title: str | None = None, body: str | None = None) -> Note | None:
        n = self.notes.get(note_id)
        if not n:
            return None
        if title is not None:
            n.title = title
        if body is not None:
            n.body = body
        n.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return n

    def delete(self, note_id: str) -> bool:
        if note_id in self.notes:
            del self.notes[note_id]
            self._save()
            return True
        return False

    def search(self, query: str) -> list[Note]:
        q = query.lower()
        return [
            n for n in self.notes.values()
            if q in n.title.lower() or q in n.body.lower() or any(q in t.lower() for t in n.tags)
        ]

    def list_all(self) -> list[Note]:
        return sorted(self.notes.values(), key=lambda x: x.updated_at, reverse=True)

    def meeting_prompt(self, raw_notes: str) -> str:
        return (
            "Uspořádej zápis z meetingu do strukturované podoby:\n"
            "1) Účastníci (pokud jdou poznat)\n"
            "2) Hlavní body\n"
            "3) Rozhodnutí\n"
            "4) Action items (kdo + co + deadline pokud je)\n\n"
            f"Surové poznámky:\n{raw_notes}"
        )

    def summarize_prompt(self, note_id: str) -> str:
        n = self.notes.get(note_id)
        if not n:
            return "Poznámka nenalezena."
        return f"Shrň tuto poznámku:\n\n# {n.title}\n{n.body}"
