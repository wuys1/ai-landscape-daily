from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from ai_landscape_daily.collectors.base import CollectionResult, Collector
from ai_landscape_daily.models import SourceItem


class RSSCollector(Collector):
    name = "rss"

    def __init__(self, feeds: list[dict]):
        self.feeds = feeds

    def collect(self) -> CollectionResult:
        items: list[SourceItem] = []
        failures: list[tuple[str, str, str]] = []
        for feed in self.feeds:
            source_name = feed["name"]
            channel = feed.get("channel", "industry")
            try:
                parsed = feedparser.parse(feed["url"])
                if parsed.bozo and parsed.bozo_exception:
                    raise RuntimeError(str(parsed.bozo_exception))
                for entry in parsed.entries[:30]:
                    items.append(
                        SourceItem(
                            title=entry.get("title", "Untitled"),
                            url=entry.get("link", feed["url"]),
                            source_name=source_name,
                            source_channel=channel,
                            published_at=_parse_date(entry),
                            summary=entry.get("summary", ""),
                            author=entry.get("author", ""),
                            tags=[tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")],
                            metadata={"feed_url": feed["url"], "source_weight": feed.get("weight", 1.0)},
                        )
                    )
            except Exception as exc:  # noqa: BLE001 - source isolation is intentional.
                failures.append((source_name, channel, str(exc)))
        return CollectionResult(items=items, failures=failures)


def _parse_date(entry: dict) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (TypeError, ValueError):
            continue
    return None
