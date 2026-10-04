"""Command palette – quick actions for CYPHERpc."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Awaitable


@dataclass
class Command:
    id: str
    title: str
    description: str = ""
    keywords: list[str] | None = None
    handler: Callable[..., Any] | None = None


class CommandPalette:
    def __init__(self) -> None:
        self.commands: list[Command] = []

    def register(self, cmd: Command) -> None:
        self.commands.append(cmd)

    def search(self, query: str) -> list[Command]:
        q = query.lower().strip()
        if not q:
            return list(self.commands)
        out = []
        for c in self.commands:
            hay = " ".join([c.id, c.title, c.description] + (c.keywords or [])).lower()
            if q in hay:
                out.append(c)
        return out

    def list_all(self) -> list[dict[str, str]]:
        return [{"id": c.id, "title": c.title, "description": c.description} for c in self.commands]


def build_default_palette(
    *,
    toggle_ai: Callable | None = None,
    toggle_privacy: Callable | None = None,
    emergency_stop: Callable | None = None,
    show_cc: Callable | None = None,
    new_chat: Callable | None = None,
    profile_gaming: Callable | None = None,
    profile_school: Callable | None = None,
    profile_privacy: Callable | None = None,
    fortnite: Callable | None = None,
) -> CommandPalette:
    p = CommandPalette()
    defs = [
        ("ai.toggle", "Zapnout/vypnout AI", "F8", toggle_ai),
        ("privacy.toggle", "Privacy Mode", "vypne vision a mikrofon", toggle_privacy),
        ("emergency.stop", "Emergency Stop", "zastaví vše", emergency_stop),
        ("cc.show", "Control Center", "stav systému", show_cc),
        ("chat.new", "Nová konverzace", "", new_chat),
        ("profile.gaming", "Profil: Gaming", "", profile_gaming),
        ("profile.school", "Profil: School", "", profile_school),
        ("profile.privacy", "Profil: Privacy", "", profile_privacy),
        ("game.fortnite", "Fortnite kouč", "pozice, heal, rotace", fortnite),
    ]
    for cid, title, desc, handler in defs:
        if handler:
            p.register(Command(id=cid, title=title, description=desc, handler=handler))
    return p
