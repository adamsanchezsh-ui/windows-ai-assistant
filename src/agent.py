"""CYPHERpc central AI agent – tools, memory, user settings (Grok-like)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from src.model import Message, ModelRouter, ModelResponse
from src.settings import Settings
from src.core.memory import MemoryStore
from src.core.personality import Personality, Style
from src.core.model_selector import ModelSelector
from src.core.permissions import PermissionManager
from src.core.user_settings import UserSettingsStore

logger = logging.getLogger(__name__)


class AIMode(str, Enum):
    NORMAL = "normal"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    RESEARCH = "research"
    SCHOOL = "school"
    GAMING = "gaming"
    PC_CONTROL = "pc_control"
    CREATIVE = "creative"


SYSTEM_PROMPTS: dict[AIMode, str] = {
    AIMode.NORMAL: (
        "Jsi pokročilý AI asistent pro Windows PC na úrovni ChatGPT/Claude/Grok. "
        "Umíš konverzovat, vysvětlovat, programovat, plánovat, analyzovat a ovládat PC."
    ),
    AIMode.REASONING: (
        "Reasoning režim: rozkládej problémy na kroky, uváděj předpoklady, "
        "zvažuj alternativy a navrhuj nejlepší řešení s odůvodněním."
    ),
    AIMode.CODING: (
        "Coding expert: čistý kód, best practices, edge cases, rizika."
    ),
    AIMode.VISION: (
        "Vision: popisuj UI, OCR text, layout a navrhuj konkrétní akce."
    ),
    AIMode.RESEARCH: (
        "Research: rozlišuj znalosti modelu vs. web. Vždy cituj zdroje."
    ),
    AIMode.SCHOOL: (
        "Učitel: vysvětluj podle obtížnosti, povzbuzuj, kontroluj pochopení."
    ),
    AIMode.GAMING: (
        "Herní kouč: rady, route, objective. Žádný cheating ani anti-cheat bypass."
    ),
    AIMode.PC_CONTROL: (
        "PC control: nástroje ano, rizikové akce jen s potvrzením."
    ),
    AIMode.CREATIVE: (
        "Kreativní režim: příběhy, nápady, texty. Buď originální."
    ),
}


@dataclass
class Conversation:
    id: str
    title: str = "Nová konverzace"
    messages: list[Message] = field(default_factory=list)
    mode: AIMode = AIMode.NORMAL


@dataclass
class ToolPermission:
    name: str
    allowed: bool = True
    requires_confirmation: bool = False


class Agent:
    def __init__(
        self,
        settings: Settings,
        router: ModelRouter,
        memory: MemoryStore | None = None,
        personality: Personality | None = None,
        model_selector: ModelSelector | None = None,
        permission_manager: PermissionManager | None = None,
        user_settings: UserSettingsStore | None = None,
    ):
        self.settings = settings
        self.router = router
        self.memory = memory
        self.personality = personality or Personality()
        self.model_selector = model_selector or ModelSelector(primary=settings.primary_model)
        self.perm_manager = permission_manager or PermissionManager()
        self.user_settings = user_settings

        self.enabled = True
        self.mode = AIMode.NORMAL
        self.conversations: dict[str, Conversation] = {}
        self.active_conversation_id: str | None = None
        self.tools: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.permissions: dict[str, ToolPermission] = {}
        self._confirmation_callback: Callable[[str], Awaitable[bool]] | None = None
        self.active_game: str | None = None
        self._game_instructions: str = ""
        self.last_model_used: str = settings.primary_model
        self.auto_model_select = True

    def set_active_game(self, game_name: str | None, instructions: str = "") -> None:
        self.active_game = game_name
        self._game_instructions = instructions or ""
        if game_name:
            self.set_mode(AIMode.GAMING)

    def set_confirmation_callback(self, cb: Callable[[str], Awaitable[bool]]) -> None:
        self._confirmation_callback = cb

    def register_tool(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        requires_confirmation: bool = False,
        allowed: bool = True,
    ) -> None:
        self.tools[name] = func
        self.permissions[name] = ToolPermission(
            name=name, allowed=allowed, requires_confirmation=requires_confirmation
        )

    def new_conversation(self, title: str = "Nová konverzace") -> Conversation:
        import uuid
        cid = str(uuid.uuid4())
        conv = Conversation(id=cid, title=title, mode=self.mode)
        self.conversations[cid] = conv
        self.active_conversation_id = cid
        return conv

    def get_active(self) -> Conversation | None:
        if self.active_conversation_id:
            return self.conversations.get(self.active_conversation_id)
        return None

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def set_mode(self, mode: AIMode | str) -> None:
        if isinstance(mode, str):
            mode = AIMode(mode.lower())
        self.mode = mode
        conv = self.get_active()
        if conv:
            conv.mode = mode

    def set_style(self, style: str) -> None:
        try:
            self.personality.style = Style(style.lower())
        except ValueError:
            pass
        if self.user_settings:
            self.user_settings.update(style=style.lower())

    async def _maybe_confirm(self, tool_name: str, description: str) -> bool:
        perm = self.permissions.get(tool_name)
        if not perm or not perm.requires_confirmation:
            return True
        if self._confirmation_callback:
            return await self._confirmation_callback(
                f"Potvrdit akci [{tool_name}]: {description}?"
            )
        logger.warning("No confirmation callback – denying %s", tool_name)
        return False

    async def run_tool(self, name: str, **kwargs: Any) -> Any:
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        perm = self.permissions.get(name)
        if perm and not perm.allowed:
            raise PermissionError(f"Tool {name} is disabled")
        if perm and perm.requires_confirmation:
            ok = await self._maybe_confirm(name, str(kwargs))
            if not ok:
                return {"status": "cancelled", "reason": "User denied confirmation"}
        return await self.tools[name](**kwargs)

    def _build_messages(self, conv: Conversation, user_text: str) -> list[Message]:
        system = SYSTEM_PROMPTS.get(conv.mode, SYSTEM_PROMPTS[AIMode.NORMAL])

        # Grok-like user settings (custom instructions, style, about user)
        if self.user_settings:
            system += "\n\n" + self.user_settings.settings.build_system_addon()
        else:
            system += "\n" + self.personality.system_addon()

        if self.memory and self.memory.enabled:
            mem_ctx = self.memory.as_context()
            if mem_ctx:
                system += "\n\n" + mem_ctx

        if self.active_game and self._game_instructions:
            system += (
                f"\n\n=== AKTIVNÍ HRA: {self.active_game.upper()} ===\n"
                + self._game_instructions
            )

        if self.settings.privacy_mode:
            system += "\n\n[PRIVACY MODE – vision a voice listening vypnuté.]"

        msgs = [Message(role="system", content=system)]
        history = conv.messages[-(self.settings.ai.max_history) :]
        msgs.extend(history)
        msgs.append(Message(role="user", content=user_text))
        return msgs

    async def chat(self, user_text: str, conversation_id: str | None = None) -> str:
        if not self.enabled:
            return "CYPHERpc AI je vypnutá. Stiskni F8 nebo zapni AI v Control Center."

        if conversation_id:
            conv = self.conversations.get(conversation_id)
            if not conv:
                raise ValueError("Conversation not found")
            self.active_conversation_id = conversation_id
        else:
            conv = self.get_active()
            if not conv:
                conv = self.new_conversation()

        messages = self._build_messages(conv, user_text)

        model_spec = None
        if self.auto_model_select:
            task = self.model_selector.detect_task(user_text, mode=self.mode.value)
            model_spec = self.model_selector.select(task, auto=True)

        response: ModelResponse = await self.router.chat(messages, model_spec=model_spec)
        self.last_model_used = f"{response.provider}:{response.model}"

        conv.messages.append(Message(role="user", content=user_text))
        conv.messages.append(Message(role="assistant", content=response.content))

        if len(conv.messages) <= 2 and conv.title == "Nová konverzace":
            conv.title = user_text[:60] + ("…" if len(user_text) > 60 else "")

        return response.content

    def status(self) -> dict[str, Any]:
        st = {
            "enabled": self.enabled,
            "mode": self.mode.value,
            "model": self.last_model_used or self.router.current_model_name(),
            "providers": self.router.list_available(),
            "privacy_mode": self.settings.privacy_mode,
            "vision": self.settings.ai.vision_mode,
            "voice": self.settings.voice.enabled,
            "memory": bool(self.memory and self.memory.enabled),
            "style": self.personality.style.value,
            "active_conversation": self.active_conversation_id,
            "active_game": self.active_game,
            "auto_model_select": self.auto_model_select,
        }
        if self.user_settings:
            us = self.user_settings.settings
            st["assistant_name"] = us.behavior.name
            st["user_name"] = us.about.name
            st["response_style"] = us.response.style
            st["tone"] = us.response.tone
        return st
