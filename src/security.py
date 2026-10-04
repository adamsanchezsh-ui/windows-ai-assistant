"""Security module: suspicious process/file checks, quarantine, Defender integration."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import psutil

logger = logging.getLogger(__name__)


class SecurityModule:
    def __init__(self, quarantine_dir: Path, use_defender: bool = True):
        self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.use_defender = use_defender

    def list_suspicious_processes(self) -> list[dict[str, Any]]:
        """Heuristic scan – high CPU + unknown path, etc."""
        suspicious = []
        for proc in psutil.process_iter(["pid", "name", "exe", "cpu_percent", "cmdline"]):
            try:
                info = proc.info
                # Very basic heuristic placeholder
                if info.get("cpu_percent", 0) > 80 and info.get("exe") is None:
                    suspicious.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "reason": "High CPU without clear executable path",
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return suspicious

    def quarantine_file(self, path: Path) -> dict[str, Any]:
        """Move file to quarantine instead of deleting."""
        if not path.exists():
            return {"status": "error", "message": "File not found"}
        dest = self.quarantine_dir / path.name
        counter = 1
        while dest.exists():
            dest = self.quarantine_dir / f"{path.stem}_{counter}{path.suffix}"
            counter += 1
        shutil.move(str(path), str(dest))
        logger.info("Quarantined %s -> %s", path, dest)
        return {"status": "ok", "quarantine_path": str(dest)}

    def scan_with_defender(self, path: Path) -> dict[str, Any]:
        """Invoke Windows Defender if available. Never disables it."""
        if not self.use_defender:
            return {"status": "skipped", "reason": "Defender integration disabled"}
        try:
            import subprocess
            # MpCmdRun is the Defender CLI
            result = subprocess.run(
                [
                    r"C:\Program Files\Windows Defender\MpCmdRun.exe",
                    "-Scan",
                    "-ScanType", "3",
                    "-File", str(path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "status": "ok",
                "returncode": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-500:],
            }
        except FileNotFoundError:
            return {"status": "unavailable", "message": "Windows Defender CLI not found"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
