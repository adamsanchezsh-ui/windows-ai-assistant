"""Safe browser assistant helpers (no automatic sensitive actions)."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class BrowserAssistant:
    """Helps with search queries and page summarization prompts."""

    def search_url(self, query: str, engine: str = "duckduckgo") -> str:
        q = quote_plus(query)
        if engine == "google":
            return f"https://www.google.com/search?q={q}"
        return f"https://duckduckgo.com/?q={q}"

    def summarize_prompt(self, url: str, content: str) -> str:
        return (
            f"Shrň obsah webové stránky {url}. "
            f"Uváděj klíčová fakta a zdroje, pokud jsou v textu.\n\n{content[:8000]}"
        )

    def explain_prompt(self, content: str) -> str:
        return f"Vysvětli následující obsah srozumitelně:\n\n{content[:8000]}"
