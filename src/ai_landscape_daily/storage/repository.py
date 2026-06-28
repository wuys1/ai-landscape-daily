from __future__ import annotations

import json
import sqlite3
from datetime import date

from ai_landscape_daily.models import RankingEntry, Signal, SourceItem, TopicNode
from ai_landscape_daily.normalize import canonical_url, item_hash, titles_similar


def _dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(value: str | None, default: object) -> object:
    if not value:
        return default
    return json.loads(value)


def upsert_source_item(conn: sqlite3.Connection, item: SourceItem) -> int:
    canon = canonical_url(item.url)
    digest = item_hash(item.title, canon)
    attribution = [{
        "source_name": item.source_name,
        "source_channel": item.source_channel,
        "url": item.url,
    }]
    existing = conn.execute(
        "SELECT * FROM source_items WHERE item_hash=? OR canonical_url=?",
        (digest, canon),
    ).fetchone()
    if not existing:
        similar = conn.execute(
            "SELECT * FROM source_items WHERE source_channel=? ORDER BY id DESC LIMIT 100",
            (item.source_channel,),
        ).fetchall()
        existing = next((row for row in similar if titles_similar(row["title"], item.title)), None)

    if existing:
        previous = list(_loads(existing["attribution_json"], []))
        seen = {(entry.get("source_name"), entry.get("url")) for entry in previous}
        for entry in attribution:
            key = (entry["source_name"], entry["url"])
            if key not in seen:
                previous.append(entry)
        conn.execute(
            """
            UPDATE source_items
            SET summary=COALESCE(NULLIF(?, ''), summary),
                tags_json=?,
                metadata_json=?,
                attribution_json=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (_clean(item.summary), _dumps(item.tags), _dumps(item.metadata), _dumps(previous), existing["id"]),
        )
        conn.commit()
        return int(existing["id"])

    cur = conn.execute(
        """
        INSERT INTO source_items
          (item_hash, canonical_url, title, summary, source_name, source_channel, published_at,
           author, tags_json, metadata_json, attribution_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            digest,
            canon,
            item.title.strip(),
            _clean(item.summary),
            item.source_name,
            item.source_channel,
            item.published_iso(),
            item.author,
            _dumps(item.tags),
            _dumps(item.metadata),
            _dumps(attribution),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _clean(value: str | None) -> str:
    return (value or "").strip()


def record_failure(conn: sqlite3.Connection, source_name: str, source_channel: str, error: str) -> None:
    conn.execute(
        "INSERT INTO collection_failures (source_name, source_channel, error) VALUES (?, ?, ?)",
        (source_name, source_channel, error[:1000]),
    )
    conn.commit()


def list_items(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM source_items ORDER BY published_at DESC, id DESC").fetchall()


def list_items_by_ids(conn: sqlite3.Connection, item_ids: list[int]) -> list[sqlite3.Row]:
    if not item_ids:
        return []
    placeholders = ", ".join("?" for _ in item_ids)
    return conn.execute(
        f"SELECT * FROM source_items WHERE id IN ({placeholders}) ORDER BY published_at DESC, id DESC",
        sorted(set(item_ids)),
    ).fetchall()


def replace_signals(conn: sqlite3.Connection, signals: list[Signal]) -> None:
    conn.execute("DELETE FROM signals")
    conn.executemany(
        """
        INSERT INTO signals
          (item_id, topic, entities_json, tags_json, signal_type, summary, contribution, confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                signal.item_id,
                signal.topic,
                _dumps(signal.entities),
                _dumps(signal.tags),
                signal.signal_type,
                signal.summary,
                signal.contribution,
                signal.confidence,
            )
            for signal in signals
        ],
    )
    conn.commit()


def replace_topics(conn: sqlite3.Connection, report_date: date, topics: list[TopicNode]) -> None:
    conn.execute("DELETE FROM topic_items WHERE topic_id IN (SELECT id FROM topics WHERE report_date=?)", (report_date.isoformat(),))
    conn.execute("DELETE FROM topics WHERE report_date=?", (report_date.isoformat(),))
    for topic in topics:
        cur = conn.execute(
            """
            INSERT INTO topics
              (report_date, slug, name, summary, score, trend, score_components_json,
               channel_counts_json, tags_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_date.isoformat(),
                topic.slug,
                topic.name,
                topic.summary,
                topic.score,
                topic.trend,
                _dumps(topic.score_components),
                _dumps(topic.channel_counts),
                _dumps(topic.tags),
            ),
        )
        topic_id = int(cur.lastrowid)
        conn.executemany(
            "INSERT OR IGNORE INTO topic_items (topic_id, item_id, evidence_summary) VALUES (?, ?, ?)",
            [(topic_id, item_id, topic.summary) for item_id in topic.evidence_item_ids],
        )
    conn.commit()


def replace_rankings(conn: sqlite3.Connection, report_date: date, entries: list[RankingEntry]) -> None:
    conn.execute("DELETE FROM rankings WHERE report_date=?", (report_date.isoformat(),))
    conn.executemany(
        """
        INSERT INTO rankings
          (report_date, scope, channel, rank, item_id, topic_slug, title, heat_score, tags_json, summary, source_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                report_date.isoformat(),
                entry.scope,
                entry.channel,
                entry.rank,
                entry.item_id,
                entry.topic_slug,
                entry.title,
                entry.heat_score,
                _dumps(entry.tags),
                entry.summary,
                entry.source_url,
            )
            for entry in entries
        ],
    )
    conn.commit()


def save_report(
    conn: sqlite3.Connection,
    report_date: date,
    output_dir: str,
    overview_path: str,
    snapshot_path: str | None,
    report_url: str | None,
    metadata: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO daily_reports
          (report_date, output_dir, overview_path, snapshot_path, report_url, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(report_date) DO UPDATE SET
          output_dir=excluded.output_dir,
          overview_path=excluded.overview_path,
          snapshot_path=excluded.snapshot_path,
          report_url=excluded.report_url,
          metadata_json=excluded.metadata_json
        """,
        (report_date.isoformat(), output_dir, overview_path, snapshot_path, report_url, _dumps(metadata)),
    )
    conn.commit()
