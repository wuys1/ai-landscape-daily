from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SourceItem:
    title: str
    url: str
    source_name: str
    source_channel: str
    published_at: datetime | None = None
    summary: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def published_iso(self) -> str | None:
        if not self.published_at:
            return None
        return self.published_at.astimezone(timezone.utc).isoformat()


@dataclass
class Signal:
    item_id: int
    topic: str
    entities: list[str]
    tags: list[str]
    signal_type: str
    summary: str
    contribution: str
    confidence: float


@dataclass
class TopicNode:
    slug: str
    name: str
    summary: str
    score: float
    trend: str
    score_components: dict[str, float]
    channel_counts: dict[str, int]
    tags: list[str]
    evidence_item_ids: list[int]


@dataclass
class RankingEntry:
    scope: str
    channel: str | None
    rank: int
    item_id: int
    topic_slug: str | None
    title: str
    heat_score: float
    tags: list[str]
    summary: str
    source_url: str
