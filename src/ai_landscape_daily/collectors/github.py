from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from ai_landscape_daily.collectors.base import CollectionResult, Collector
from ai_landscape_daily.models import SourceItem


class GitHubTrendingCollector(Collector):
    name = "github_trending"

    def __init__(self, config: dict):
        self.config = config

    def collect(self) -> CollectionResult:
        language = self.config.get("language", "")
        since = self.config.get("since", "daily")
        url = f"https://github.com/trending/{language}?since={since}" if language else f"https://github.com/trending?since={since}"
        try:
            response = httpx.get(url, timeout=20, headers={"User-Agent": "ai-landscape-daily"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            items: list[SourceItem] = []
            for article in soup.select("article.Box-row")[:25]:
                title_node = article.select_one("h2 a")
                if not title_node:
                    continue
                repo_path = re.sub(r"\s+", "", title_node.get_text(strip=True))
                repo_url = "https://github.com" + title_node.get("href", "")
                description = article.select_one("p")
                stars_text = article.get_text(" ", strip=True)
                stars = _first_number(stars_text)
                items.append(
                    SourceItem(
                        title=repo_path,
                        url=repo_url,
                        source_name="GitHub Trending",
                        source_channel="github",
                        summary=description.get_text(" ", strip=True) if description else "",
                        tags=self.config.get("topics", []),
                        metadata={"stars_hint": stars, "source_weight": self.config.get("weight", 0.9)},
                    )
                )
            return CollectionResult(items=items, failures=[])
        except Exception as exc:  # noqa: BLE001
            return CollectionResult(items=[], failures=[("GitHub Trending", "github", str(exc))])


def _first_number(text: str) -> int:
    match = re.search(r"([0-9][0-9,]*)", text)
    return int(match.group(1).replace(",", "")) if match else 0
