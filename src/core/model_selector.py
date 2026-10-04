"""Automatic model selection by task type."""

from __future__ import annotations

from enum import Enum
from typing import Any


class TaskType(str, Enum):
    QUICK = "quick"           # krátké odpovědi
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    RESEARCH = "research"
    CREATIVE = "creative"
    CHAT = "chat"


# Default mapping – uživatel může přepsat v config
DEFAULT_MODEL_MAP: dict[TaskType, str] = {
    TaskType.QUICK: "openai:gpt-4o-mini",
    TaskType.CHAT: "openai:gpt-4o",
    TaskType.REASONING: "anthropic:claude-3-5-sonnet",
    TaskType.CODING: "openai:gpt-4o",
    TaskType.VISION: "openai:gpt-4o",
    TaskType.RESEARCH: "openai:gpt-4o",
    TaskType.CREATIVE: "openai:gpt-4o",
}


class ModelSelector:
    def __init__(self, mapping: dict[str, str] | None = None, primary: str = "openai:gpt-4o"):
        self.primary = primary
        self.mapping: dict[TaskType, str] = dict(DEFAULT_MODEL_MAP)
        if mapping:
            for k, v in mapping.items():
                try:
                    self.mapping[TaskType(k)] = v
                except ValueError:
                    pass

    def select(self, task: TaskType | str, auto: bool = True) -> str:
        if not auto:
            return self.primary
        if isinstance(task, str):
            try:
                task = TaskType(task)
            except ValueError:
                return self.primary
        return self.mapping.get(task, self.primary)

    def detect_task(self, user_text: str, mode: str = "normal") -> TaskType:
        t = user_text.lower()
        if mode in ("coding",) or any(k in t for k in ("kód", "code", "python", "bug", "function", "debug")):
            return TaskType.CODING
        if mode in ("vision",) or any(k in t for k in ("screenshot", "obrazovka", "vidíš", "ocr")):
            return TaskType.VISION
        if mode in ("research",) or any(k in t for k in ("vyhledej", "najdi na webu", "aktuální", "zprávy")):
            return TaskType.RESEARCH
        if mode in ("reasoning",) or any(k in t for k in ("promysli", "plán", "proč", "analýza")):
            return TaskType.REASONING
        if mode in ("creative",) or any(k in t for k in ("příběh", "báseň", "nápad", "vymysli")):
            return TaskType.CREATIVE
        if len(user_text) < 40:
            return TaskType.QUICK
        return TaskType.CHAT
