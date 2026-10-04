"""Safe file management helpers."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FileManager:
    def __init__(self, confirm_delete: bool = True):
        self.confirm_delete = confirm_delete

    def search(self, root: Path, pattern: str, limit: int = 50) -> list[str]:
        results = []
        for p in root.rglob(pattern):
            results.append(str(p))
            if len(results) >= limit:
                break
        return results

    def create_folder(self, path: Path) -> dict[str, Any]:
        path.mkdir(parents=True, exist_ok=True)
        return {"status": "ok", "path": str(path)}

    def rename(self, src: Path, dst: Path) -> dict[str, Any]:
        src.rename(dst)
        return {"status": "ok", "from": str(src), "to": str(dst)}

    def copy(self, src: Path, dst: Path) -> dict[str, Any]:
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        return {"status": "ok", "from": str(src), "to": str(dst)}

    def move(self, src: Path, dst: Path) -> dict[str, Any]:
        shutil.move(str(src), str(dst))
        return {"status": "ok", "from": str(src), "to": str(dst)}

    def read_text(self, path: Path, max_bytes: int = 100_000) -> str:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", errors="replace")

    def delete(self, path: Path, confirmed: bool = False) -> dict[str, Any]:
        if self.confirm_delete and not confirmed:
            return {"status": "needs_confirmation", "path": str(path)}
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        return {"status": "ok", "deleted": str(path)}
