from __future__ import annotations

from datetime import datetime, timezone

from ai_landscape_daily.models import SourceItem
from ai_landscape_daily.normalize import canonical_url, item_hash, titles_similar
from ai_landscape_daily.storage import repository
from ai_landscape_daily.storage.db import connect, migrate


def test_canonical_url_removes_tracking_params():
    url = canonical_url("HTTPS://Example.com/path/?utm_source=x&b=2&a=1#section")
    assert url == "https://example.com/path?a=1&b=2"


def test_item_hash_is_stable_after_tracking_removal():
    left = item_hash("AI News", "https://example.com/a?utm_campaign=x")
    right = item_hash(" AI   News ", "https://example.com/a")
    assert left == right


def test_title_similarity():
    assert titles_similar("OpenAI releases agent tools", "OpenAI releases new agent tooling")


def test_schema_and_basic_persistence(tmp_path):
    conn = connect(tmp_path / "daily.sqlite3")
    migrate(conn)
    item_id = repository.upsert_source_item(
        conn,
        SourceItem(
            title="OpenAI releases agent tools",
            url="https://example.com/a?utm_source=news",
            source_name="OpenAI",
            source_channel="official",
            published_at=datetime.now(timezone.utc),
            summary="Agent tooling update.",
            tags=["agents"],
        ),
    )
    duplicate_id = repository.upsert_source_item(
        conn,
        SourceItem(
            title="OpenAI releases agent tools",
            url="https://example.com/a",
            source_name="Mirror",
            source_channel="industry",
            summary="Cross-post.",
        ),
    )
    rows = repository.list_items(conn)
    assert duplicate_id == item_id
    assert len(rows) == 1
    assert "Mirror" in rows[0]["attribution_json"]
