"""CYPHERpc Control Center – status dashboard data model."""

from __future__ import annotations

from typing import Any


class ControlCenter:
    """
    Jedna hlavní obrazovka se stavem:
    CYPHERpc, AI, MODEL, VOICE, WAKE WORD, VISION, OVERLAY, GAME, MONITOR, CPU/RAM/GPU
    """

    def __init__(self) -> None:
        self.app_online = True

    def build_status(
        self,
        *,
        ai_online: bool,
        model: str,
        mode: str,
        voice: dict[str, Any],
        vision_mode: str,
        overlay_on: bool,
        game: str | None,
        monitor: int,
        cpu: float,
        ram: float,
        gpu: float | None,
        privacy_mode: bool,
        profile: str,
        providers: list[str],
    ) -> dict[str, Any]:
        return {
            "CYPHERpc": "ONLINE" if self.app_online else "OFFLINE",
            "AI": "ONLINE" if ai_online else "OFFLINE",
            "MODEL": model,
            "MODE": mode,
            "VOICE": "ON" if voice.get("enabled") else "OFF",
            "WAKE_WORD": "ON" if voice.get("wake_word") else "OFF",
            "MIC_LISTENING": voice.get("listening", False),
            "VISION": vision_mode.upper(),
            "OVERLAY": "ON" if overlay_on else "OFF",
            "GAME": game or "—",
            "MONITOR": monitor,
            "CPU": f"{cpu:.0f}%",
            "RAM": f"{ram:.0f}%",
            "GPU": f"{gpu:.0f}%" if gpu is not None else "N/A",
            "PRIVACY": "ON" if privacy_mode else "OFF",
            "PROFILE": profile,
            "PROVIDERS": providers,
        }

    def format_cli(self, status: dict[str, Any]) -> str:
        lines = [
            "┌── CYPHERpc Control Center ───────────────┐",
            f"│  CYPHERpc : {status['CYPHERpc']:<12} AI : {status['AI']:<10} │",
            f"│  MODEL    : {status['MODEL']:<28} │",
            f"│  MODE     : {status['MODE']:<12} PROFILE : {status['PROFILE']:<8} │",
            f"│  VOICE    : {status['VOICE']:<6} WAKE : {status['WAKE_WORD']:<5} MIC : {str(status['MIC_LISTENING']):<5} │",
            f"│  VISION   : {status['VISION']:<12} OVERLAY : {status['OVERLAY']:<6} │",
            f"│  GAME     : {status['GAME']:<12} MONITOR : {status['MONITOR']:<6} │",
            f"│  CPU {status['CPU']:<6} RAM {status['RAM']:<6} GPU {status['GPU']:<8} │",
            f"│  PRIVACY  : {status['PRIVACY']:<28} │",
            "└────────────────────────────────────────┘",
        ]
        return "\n".join(lines)
