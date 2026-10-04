"""Performance monitoring and mode management."""

from __future__ import annotations

import logging
from typing import Any, Literal

import psutil

logger = logging.getLogger(__name__)

Mode = Literal["quality", "balanced", "performance"]


class PerformanceManager:
    def __init__(self, mode: Mode = "balanced"):
        self.mode = mode

    def set_mode(self, mode: Mode) -> None:
        self.mode = mode
        logger.info("Performance mode: %s", mode)

    def get_stats(self) -> dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        gpu = None
        try:
            # Optional: nvidia-smi or GPUtil
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                text=True,
                timeout=2,
            )
            parts = out.strip().split(",")
            if len(parts) >= 2:
                gpu = {"util": float(parts[0]), "mem_used_mb": float(parts[1])}
        except Exception:
            pass

        return {
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "net_sent_mb": round(net.bytes_sent / (1024**2), 1),
            "net_recv_mb": round(net.bytes_recv / (1024**2), 1),
            "gpu": gpu,
            "mode": self.mode,
        }
