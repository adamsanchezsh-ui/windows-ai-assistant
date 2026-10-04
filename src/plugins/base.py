"""Modular plugin API."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.core.permissions import Permission

logger = logging.getLogger(__name__)


@dataclass
class PluginMeta:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    permissions: list[Permission] = field(default_factory=list)


class Plugin(ABC):
    """Base class for CYPHERpc plugins (Spotify, Discord, Browser, Smart Home…)."""

    meta: PluginMeta

    def __init__(self) -> None:
        self.enabled = False

    @abstractmethod
    async def setup(self, context: dict[str, Any]) -> None:
        """Called once when plugin is loaded."""

    @abstractmethod
    async def on_enable(self) -> None:
        ...

    @abstractmethod
    async def on_disable(self) -> None:
        ...

    async def handle_command(self, command: str, args: dict[str, Any] | None = None) -> Any:
        """Optional command handler."""
        return {"status": "not_implemented"}

    def tools(self) -> dict[str, Any]:
        """Return dict of tool_name -> async callable for agent registration."""
        return {}


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        self._plugins[plugin.meta.id] = plugin
        logger.info("Plugin registered: %s", plugin.meta.id)

    def get(self, plugin_id: str) -> Plugin | None:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> list[dict[str, Any]]:
        return [
            {
                "id": p.meta.id,
                "name": p.meta.name,
                "version": p.meta.version,
                "description": p.meta.description,
                "enabled": p.enabled,
                "permissions": [x.value for x in p.meta.permissions],
            }
            for p in self._plugins.values()
        ]

    async def enable(self, plugin_id: str) -> bool:
        p = self._plugins.get(plugin_id)
        if not p:
            return False
        await p.on_enable()
        p.enabled = True
        return True

    async def disable(self, plugin_id: str) -> bool:
        p = self._plugins.get(plugin_id)
        if not p:
            return False
        await p.on_disable()
        p.enabled = False
        return True

    def all_tools(self) -> dict[str, Any]:
        tools = {}
        for p in self._plugins.values():
            if p.enabled:
                tools.update(p.tools())
        return tools
