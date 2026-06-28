from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

from ai_landscape_daily.models import RankingEntry, TopicNode
from ai_landscape_daily.normalize import slugify


def build_topics_and_rankings(
    rows: list[sqlite3.Row],
    signals: list,
    report_date: date,
    scoring_config: dict,
) -> tuple[list[TopicNode], list[RankingEntry]]:
    item_map = {int(row["id"]): row for row in rows}
    by_topic: dict[str, list] = defaultdict(list)
    topic_names: dict[str, str] = {}
    for signal in signals:
        topic_name = _normalize_topic(signal.topic, scoring_config)
        topic_slug = slugify(topic_name)
        by_topic[topic_slug].append(signal)
        topic_names.setdefault(topic_slug, topic_name)

    topics: list[TopicNode] = []
    for topic_slug, grouped in by_topic.items():
        topic_name = topic_names[topic_slug]
        evidence_ids = sorted({signal.item_id for signal in grouped})
        channel_counts = Counter(item_map[item_id]["source_channel"] for item_id in evidence_ids if item_id in item_map)
        tags = _top_tags(grouped)
        components = _score_components(evidence_ids, item_map, channel_counts, report_date, scoring_config)
        score = sum(components.values())
        summary = _topic_summary(topic_name, grouped, channel_counts)
        topics.append(
            TopicNode(
                slug=topic_slug,
                name=topic_name,
                summary=summary,
                score=round(score, 2),
                trend="rising" if len(evidence_ids) >= 2 else "watch",
                score_components={key: round(value, 2) for key, value in components.items()},
                channel_counts=dict(channel_counts),
                tags=tags,
                evidence_item_ids=evidence_ids,
            )
        )
    topics.sort(key=lambda topic: topic.score, reverse=True)
    max_topics = int(scoring_config.get("max_topics", 12))
    topics = topics[:max_topics]
    rankings = _rank_items(rows, signals, topics, scoring_config)
    return topics, rankings


def _normalize_topic(topic: str, scoring_config: dict) -> str:
    aliases = scoring_config.get("topic_aliases", {})
    return aliases.get(topic.lower(), topic)


def _score_components(evidence_ids, item_map, channel_counts, report_date, scoring_config) -> dict[str, float]:
    weights = scoring_config.get("weights", {})
    channel_weights = scoring_config.get("source_channel_weights", {})
    source = max((channel_weights.get(item_map[item_id]["source_channel"], 0.6) for item_id in evidence_ids if item_id in item_map), default=0.5)
    cross = min(len(channel_counts) / 4, 1)
    frequency = min(len(evidence_ids) / 5, 1)
    freshness = _freshness(evidence_ids, item_map, report_date)
    community = min(sum(_metadata(item_map[item_id]).get("stars_hint", 0) for item_id in evidence_ids if item_id in item_map) / 1500, 1)
    momentum = min((frequency + cross + community) / 3, 1)
    raw = {
        "source_weight": source,
        "cross_source_score": cross,
        "frequency_score": frequency,
        "freshness_score": freshness,
        "momentum_score": momentum,
        "community_score": community,
    }
    return {key: raw[key] * weights.get(key, 0.1) * 100 for key in raw}


def _freshness(evidence_ids, item_map, report_date) -> float:
    scores = []
    day = datetime.combine(report_date, datetime.min.time(), tzinfo=timezone.utc)
    for item_id in evidence_ids:
        row = item_map.get(item_id)
        if not row or not row["published_at"]:
            scores.append(0.65)
            continue
        try:
            published = datetime.fromisoformat(row["published_at"])
            age_hours = abs((day - published).total_seconds()) / 3600
            scores.append(max(0.2, 1 - min(age_hours, 96) / 96))
        except ValueError:
            scores.append(0.65)
    return max(scores or [0.5])


def _rank_items(rows, signals, topics, scoring_config) -> list[RankingEntry]:
    topic_by_item = {}
    score_by_topic = {topic.slug: topic.score for topic in topics}
    for topic in topics:
        for item_id in topic.evidence_item_ids:
            topic_by_item.setdefault(item_id, topic.slug)
    signal_tags = defaultdict(list)
    signal_summaries = defaultdict(list)
    for signal in signals:
        signal_tags[signal.item_id].extend(signal.tags)
        signal_summaries[signal.item_id].append(signal.summary)

    scored = []
    for row in rows:
        item_id = int(row["id"])
        topic_slug = topic_by_item.get(item_id)
        base = score_by_topic.get(topic_slug, 35)
        channel_boost = scoring_config.get("source_channel_weights", {}).get(row["source_channel"], 0.7) * 10
        community = min(_metadata(row).get("stars_hint", 0) / 100, 10)
        scored.append((base + channel_boost + community, row, topic_slug))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    rankings: list[RankingEntry] = []
    max_overall = int(scoring_config.get("max_overall_rankings", 20))
    for rank, (score, row, topic_slug) in enumerate(scored[:max_overall], start=1):
        rankings.append(_ranking_entry("overall", None, rank, score, row, topic_slug, signal_tags, signal_summaries))
    by_channel = defaultdict(list)
    for score, row, topic_slug in scored:
        by_channel[row["source_channel"]].append((score, row, topic_slug))
    max_channel = int(scoring_config.get("max_channel_rankings", 12))
    for channel, entries in by_channel.items():
        for rank, (score, row, topic_slug) in enumerate(entries[:max_channel], start=1):
            rankings.append(_ranking_entry("channel", channel, rank, score, row, topic_slug, signal_tags, signal_summaries))
    return rankings


def _ranking_entry(scope, channel, rank, score, row, topic_slug, signal_tags, signal_summaries) -> RankingEntry:
    tags = list(dict.fromkeys(signal_tags.get(int(row["id"]), []) + _json_list(row["tags_json"])))[:6]
    return RankingEntry(
        scope=scope,
        channel=channel,
        rank=rank,
        item_id=int(row["id"]),
        topic_slug=topic_slug,
        title=row["title"],
        heat_score=round(score, 2),
        tags=tags,
        summary=_best_signal_summary(row, signal_summaries),
        source_url=row["canonical_url"],
    )


def _topic_summary(topic_name: str, grouped, channel_counts: Counter) -> str:
    channel_labels = {
        "official": "官方公告",
        "github": "GitHub",
        "papers": "论文",
        "chinese_media": "中文媒体",
        "industry": "产业媒体",
    }
    channels = "、".join(channel_labels.get(channel, channel) for channel in channel_counts.keys())
    return f"「{topic_name}」今日由 {len(grouped)} 条信号支撑，覆盖{channels or '多个'}渠道。"


def _top_tags(grouped) -> list[str]:
    counter = Counter(tag for signal in grouped for tag in signal.tags)
    return [tag for tag, _ in counter.most_common(6)]


def _metadata(row: sqlite3.Row) -> dict:
    try:
        return json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        return {}


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed]


def _best_signal_summary(row: sqlite3.Row, signal_summaries) -> str:
    summaries = signal_summaries.get(int(row["id"]), [])
    for summary in summaries:
        if any("\u4e00" <= char <= "\u9fff" for char in summary):
            return summary[:240]
    summary = (row["summary"] or row["title"]).strip()
    if any("\u4e00" <= char <= "\u9fff" for char in summary):
        return summary[:240]
    return f"来自 {row['source_name']} 的相关动态：{summary[:200]}"
