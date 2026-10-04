"""Application settings and configuration loading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


class AISettings(BaseSettings):
    default_mode: str = "normal"
    max_history: int = 50
    temperature: float = 0.7
    vision_mode: Literal["off", "on_demand", "periodic"] = "on_demand"
    periodic_interval_sec: int = 30
    memory_enabled: bool = False


class PerformanceSettings(BaseSettings):
    mode: Literal["quality", "balanced", "performance"] = "balanced"
    default_priority: Literal["normal", "high"] = "normal"


class OverlaySettings(BaseSettings):
    enabled: bool = False
    monitor: int = 1
    opacity: float = 0.85


class VoiceSettings(BaseSettings):
    enabled: bool = False
    language: str = "cs"
    volume: float = 0.8
    rate: float = 1.0
    auto_detect_language: bool = False


class SecuritySettings(BaseSettings):
    confirm_delete: bool = True
    confirm_system_change: bool = True
    confirm_send_message: bool = True
    use_defender: bool = True
    quarantine_instead_of_delete: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Secrets / providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    xai_api_key: str | None = None
    google_api_key: str | None = None
    primary_model: str = "openai:gpt-4o"
    fallback_models: str = ""
    local_api_base: str | None = None
    local_api_key: str | None = None
    app_secret_key: str = "change-me"

    # Paths
    data_dir: Path = Path("./data")
    log_dir: Path = Path("./logs")
    quarantine_dir: Path = Path("./data/quarantine")

    # Feature flags
    enable_vision: bool = True
    enable_voice: bool = True
    enable_web_search: bool = True
    enable_memory: bool = False

    default_language: str = "cs"

    # Nested (loaded from yaml or defaults)
    ai: AISettings = Field(default_factory=AISettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    overlay: OverlaySettings = Field(default_factory=OverlaySettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    privacy_mode: bool = False
    selected_monitor: int = 1

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)


def load_yaml_config(path: Path | str = "config/settings.yaml") -> dict[str, Any]:
    p = Path(path)
    if not p.exists() or yaml is None:
        return {}
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> Settings:
    """Load settings from env + optional yaml."""
    yaml_data = load_yaml_config()
    # Simple merge of known sections
    kwargs: dict[str, Any] = {}
    if "ai" in yaml_data:
        kwargs["ai"] = AISettings(**yaml_data["ai"])
    if "performance" in yaml_data:
        kwargs["performance"] = PerformanceSettings(**yaml_data["performance"])
    if "overlay" in yaml_data:
        kwargs["overlay"] = OverlaySettings(**yaml_data["overlay"])
    if "voice" in yaml_data:
        kwargs["voice"] = VoiceSettings(**yaml_data["voice"])
    if "security" in yaml_data:
        kwargs["security"] = SecuritySettings(**yaml_data["security"])
    if "privacy_mode" in yaml_data:
        kwargs["privacy_mode"] = yaml_data["privacy_mode"]
    if "monitors" in yaml_data and "selected" in yaml_data["monitors"]:
        kwargs["selected_monitor"] = yaml_data["monitors"]["selected"]

    s = Settings(**kwargs)
    s.ensure_dirs()
    return s
