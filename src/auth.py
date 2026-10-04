"""Local authentication with secure password hashing."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    # PBKDF2-HMAC-SHA256
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return salt.hex(), dk.hex()


def _verify(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, new_hash = _hash_password(password, salt)
    return hmac.compare_digest(new_hash, hash_hex)


class AuthService:
    def __init__(self, data_dir: Path, secret_key: str):
        self.data_dir = data_dir
        self.secret_key = secret_key.encode("utf-8")
        self.users_file = data_dir / "users.json"
        self.sessions: dict[str, dict[str, Any]] = {}

    def _load_users(self) -> dict[str, Any]:
        import json
        if not self.users_file.exists():
            return {}
        return json.loads(self.users_file.read_text(encoding="utf-8"))

    def _save_users(self, users: dict[str, Any]) -> None:
        import json
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self.users_file.write_text(json.dumps(users, indent=2), encoding="utf-8")

    def register(self, username: str, password: str) -> dict[str, Any]:
        users = self._load_users()
        if username in users:
            return {"status": "error", "message": "User already exists"}
        salt, pw_hash = _hash_password(password)
        users[username] = {"salt": salt, "hash": pw_hash}
        self._save_users(users)
        return {"status": "ok", "username": username}

    def login(self, username: str, password: str) -> dict[str, Any]:
        users = self._load_users()
        user = users.get(username)
        if not user or not _verify(password, user["salt"], user["hash"]):
            return {"status": "error", "message": "Invalid credentials"}
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {"username": username}
        return {"status": "ok", "token": token, "username": username}

    def validate_session(self, token: str) -> str | None:
        session = self.sessions.get(token)
        return session["username"] if session else None

    def logout(self, token: str) -> None:
        self.sessions.pop(token, None)
