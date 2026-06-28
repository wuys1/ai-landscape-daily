from __future__ import annotations

from dataclasses import dataclass

from ai_landscape_daily.models import SourceItem


@dataclass
class CollectionResult:
    items: list[SourceItem]
    failures: list[tuple[str, str, str]]


class Collector:
    name = "collector"

    def collect(self) -> CollectionResult:
        raise NotImplementedError
