"""Web research agent – search, fetch, summarize with sources. No result limits."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass
class ResearchReport:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    summary: str = ""
    sources: list[str] = field(default_factory=list)


class WebAgent:
    """
    Safe web research. Uses DuckDuckGo HTML (no API key) + optional page fetch.
    Always returns sources for verification.
    """

    def __init__(self, timeout: float = 15.0, max_results: int = 0):
        # max_results=0 means no artificial limit (fetch as many as page provides)
        self.timeout = timeout
        self.max_results = max_results  # 0 = unlimited from page

    def search_url(self, query: str, engine: str = "duckduckgo") -> str:
        q = quote_plus(query)
        if engine == "google":
            return f"https://www.google.com/search?q={q}"
        if engine == "bing":
            return f"https://www.bing.com/search?q={q}"
        return f"https://html.duckduckgo.com/html/?q={q}"

    async def search(self, query: str, engine: str = "duckduckgo") -> list[SearchResult]:
        url = self.search_url(query, engine)
        results: list[SearchResult] = []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "CYPHERpc/0.3 ResearchBot"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text

            # Lightweight parse of DDG HTML results
            # result links often in class result__a
            for m in re.finditer(
                r'href="(https?://(?!duckduckgo)[^"]+)"[^>]*>([^<]+)</a>',
                html,
                re.I,
            ):
                link, title = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
                if "duckduckgo" in link or not title:
                    continue
                results.append(SearchResult(title=title[:200], url=link, snippet=""))
                if self.max_results and len(results) >= self.max_results:
                    break

            # Snippets
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</', html, re.S | re.I)
            for i, sn in enumerate(snippets):
                if i < len(results):
                    results[i].snippet = re.sub(r"<[^>]+>", "", sn).strip()[:400]

        except Exception as e:
            logger.exception("Web search failed: %s", e)
            results.append(SearchResult(
                title="Search error",
                url="",
                snippet=str(e),
            ))
        return results

    async def fetch_page(self, url: str, max_chars: int = 0) -> str:
        """Fetch page text. max_chars=0 means full content (capped only by practical memory)."""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": "CYPHERpc/0.3 ResearchBot"},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                text = resp.text
            # Strip tags roughly
            text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
            text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if max_chars and max_chars > 0:
                return text[:max_chars]
            return text  # no artificial limit
        except Exception as e:
            return f"[Fetch error: {e}]"

    async def research(self, query: str) -> ResearchReport:
        results = await self.search(query)
        sources = [r.url for r in results if r.url]
        lines = [f"- {r.title}: {r.snippet} ({r.url})" for r in results]
        summary = f"Nalezeno {len(results)} výsledků pro: {query}\n" + "\n".join(lines)
        return ResearchReport(query=query, results=results, summary=summary, sources=sources)

    def research_prompt(self, report: ResearchReport) -> str:
        return (
            f"Na základě následujících webových výsledků odpověz na dotaz: {report.query}\n"
            f"Vždy cituj zdroje (URL). Rozlišuj fakta z vyhledávání od vlastních znalostí.\n\n"
            f"{report.summary}"
        )
