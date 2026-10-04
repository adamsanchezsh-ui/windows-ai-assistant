"""API usage monitoring – track tokens/calls, optional soft budget (0 = unlimited)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 1


@dataclass
class DailyUsage:
    day: str
    records: list[UsageRecord] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(r.prompt_tokens + r.completion_tokens for r in self.records)

    @property
    def total_calls(self) -> int:
        return sum(r.calls for r in self.records)


class APIUsageMonitor:
    """
    Tracks API usage. daily_limit=0 means unlimited (no blocking).
    Only warns when limit > 0 and exceeded.
    """

    def __init__(self, data_dir: Path, daily_limit: int = 0):
        self.path = data_dir / "api_usage.json"
        self.daily_limit = daily_limit  # 0 = no limit
        self._today = self._load_today()

    def _load_today(self) -> DailyUsage:
        today = date.today().isoformat()
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if data.get("day") == today:
                    records = [UsageRecord(**r) for r in data.get("records", [])]
                    return DailyUsage(day=today, records=records)
            except Exception:
                logger.exception("usage load")
        return DailyUsage(day=today)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({
                "day": self._today.day,
                "records": [asdict(r) for r in self._today.records],
                "total_tokens": self._today.total_tokens,
                "total_calls": self._today.total_calls,
            }, indent=2),
            encoding="utf-8",
        )

    def record(self, provider: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self._today.records.append(UsageRecord(
            provider=provider, model=model,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        ))
        self._save()

    def can_call(self) -> bool:
        if self.daily_limit <= 0:
            return True  # unlimited
        return self._today.total_calls < self.daily_limit

    def snapshot(self) -> dict[str, Any]:
        return {
            "day": self._today.day,
            "total_tokens": self._today.total_tokens,
            "total_calls": self._today.total_calls,
            "daily_limit": self.daily_limit if self.daily_limit > 0 else "unlimited",
            "remaining": (self.daily_limit - self._today.total_calls) if self.daily_limit > 0 else "unlimited",
        }
