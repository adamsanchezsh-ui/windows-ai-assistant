"""Tool permission system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Permission(str, Enum):
    READ_SCREEN = "READ_SCREEN"
    READ_FILES = "READ_FILES"
    WRITE_FILES = "WRITE_FILES"
    OPEN_APP = "OPEN_APP"
    MOVE_FILE = "MOVE_FILE"
    DELETE_FILE = "DELETE_FILE"
    SEND_MESSAGE = "SEND_MESSAGE"
    CHANGE_SETTINGS = "CHANGE_SETTINGS"
    CONTROL_INPUT = "CONTROL_INPUT"  # keyboard/mouse
    WEB_ACCESS = "WEB_ACCESS"
    PROCESS_CONTROL = "PROCESS_CONTROL"
    VOICE_LISTEN = "VOICE_LISTEN"
    CLIPBOARD = "CLIPBOARD"


# Which permissions require explicit user confirmation by default
DEFAULT_CONFIRM = {
    Permission.DELETE_FILE,
    Permission.SEND_MESSAGE,
    Permission.CHANGE_SETTINGS,
    Permission.PROCESS_CONTROL,
}


@dataclass
class PermissionState:
    permission: Permission
    allowed: bool = True
    requires_confirmation: bool = False


class PermissionManager:
    def __init__(self) -> None:
        self._states: dict[Permission, PermissionState] = {}
        for p in Permission:
            self._states[p] = PermissionState(
                permission=p,
                allowed=True,
                requires_confirmation=p in DEFAULT_CONFIRM,
            )

    def is_allowed(self, perm: Permission) -> bool:
        return self._states[perm].allowed

    def needs_confirmation(self, perm: Permission) -> bool:
        return self._states[perm].requires_confirmation

    def set_allowed(self, perm: Permission, allowed: bool) -> None:
        self._states[perm].allowed = allowed

    def set_confirmation(self, perm: Permission, required: bool) -> None:
        self._states[perm].requires_confirmation = required

    def snapshot(self) -> dict[str, Any]:
        return {
            p.value: {
                "allowed": s.allowed,
                "requires_confirmation": s.requires_confirmation,
            }
            for p, s in self._states.items()
        }

    def deny_all(self) -> None:
        """Emergency / Privacy: disable everything sensitive."""
        for s in self._states.values():
            if s.permission in (
                Permission.READ_SCREEN,
                Permission.VOICE_LISTEN,
                Permission.CONTROL_INPUT,
                Permission.DELETE_FILE,
                Permission.SEND_MESSAGE,
                Permission.CHANGE_SETTINGS,
            ):
                s.allowed = False

    def restore_defaults(self) -> None:
        for p in Permission:
            self._states[p].allowed = True
            self._states[p].requires_confirmation = p in DEFAULT_CONFIRM
