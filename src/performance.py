"""Performance monitoring and mode management."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

import psutil

logger = logging.getLogger(__name__)

Mode = Literal["quality", "balanced", "performance"]


class PerformanceManager:
    def __init__(self, mode: Mode = "balanced"):
        self.mode = mode

    def set_mode(self, mode: Mode | str) -> None:
        if mode not in ("quality", "balanced", "performance"):
            mode = "balanced"
        self.mode = mode  # type: ignore
        logger.info("Performance mode: %s", mode)

    def get_stats(self) -> dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.2)
        mem = psutil.virtual_memory()
        disk_path = "C:\\" if os.name == "nt" else "/"
        try:
            disk = psutil.disk_usage(disk_path)
            disk_percent = disk.percent
        except Exception:
            disk_percent = 0.0
        try:
            net = psutil.net_io_counters()
            net_sent = round(net.bytes_sent / (1024**2), 1)
            net_recv = round(net.bytes_recv / (1024**2), 1)
        except Exception:
            net_sent = net_recv = 0.0

        gpu = None
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                text=True,
                timeout=2,
            )
            parts = out.strip().split(",")
            if len(parts) >= 2:
                gpu = {"util": float(parts[0].strip()), "mem_used_mb": float(parts[1].strip())}
        except Exception:
            pass

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk_percent,
            "net_sent_mb": net_sent,
            "net_recv_mb": net_recv,
            "gpu": gpu,
            "mode": self.mode,
        }
