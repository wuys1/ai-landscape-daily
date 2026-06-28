from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree

import httpx

from ai_landscape_daily.collectors.base import CollectionResult, Collector
from ai_landscape_daily.models import SourceItem


class ArxivCollector(Collector):
    name = "arxiv"

    def __init__(self, config: dict):
        self.config = config

    def collect(self) -> CollectionResult:
        categories = self.config.get("categories", ["cs.AI"])
        query = "+OR+".join(f"cat:{category}" for category in categories)
        max_results = int(self.config.get("max_results", 20))
        url = (
            "https://export.arxiv.org/api/query"
            f"?search_query={query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        )
        try:
            response = httpx.get(url, timeout=20)
            response.raise_for_status()
            root = ElementTree.fromstring(response.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = []
            for entry in root.findall("atom:entry", ns):
                title = _text(entry, "atom:title", ns)
                link = _text(entry, "atom:id", ns)
                published = _text(entry, "atom:published", ns)
                summary = _text(entry, "atom:summary", ns)
                tags = [node.attrib.get("term", "") for node in entry.findall("atom:category", ns)]
                items.append(
                    SourceItem(
                        title=" ".join(title.split()),
                        url=link,
                        source_name="arXiv",
                        source_channel="papers",
                        published_at=datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None,
                        summary=" ".join(summary.split()),
                        tags=[tag for tag in tags if tag],
                        metadata={"source_weight": self.config.get("weight", 0.8)},
                    )
                )
            return CollectionResult(items=items, failures=[])
        except Exception as exc:  # noqa: BLE001
            return CollectionResult(items=[], failures=[("arXiv", "papers", str(exc))])


def _text(entry: ElementTree.Element, path: str, ns: dict[str, str]) -> str:
    node = entry.find(path, ns)
    return node.text.strip() if node is not None and node.text else ""
