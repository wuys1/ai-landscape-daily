from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_landscape_daily.models import RankingEntry, TopicNode

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"
CHANNEL_ORDER = ["official", "chinese_media", "industry", "github", "papers"]
CHANNEL_LABELS = {
    "official": "官方公告",
    "chinese_media": "中文媒体",
    "industry": "产业媒体",
    "github": "GitHub 趋势",
    "papers": "论文",
}


def render_report(
    *,
    output_dir: Path,
    report_date: date,
    rows: list[sqlite3.Row],
    topics: list[TopicNode],
    rankings: list[RankingEntry],
    channels: dict,
    failures: list[tuple[str, str, str]],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_dir in ("topics", "channels"):
        stale_path = output_dir / stale_dir
        if stale_path.exists():
            shutil.rmtree(stale_path)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    for asset in STATIC_DIR.iterdir():
        if asset.is_file():
            shutil.copy2(asset, assets_dir / asset.name)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["json"] = lambda value: json.dumps(value, ensure_ascii=False)
    item_map = {int(row["id"]): _row_dict(row) for row in rows}
    overall = [entry for entry in rankings if entry.scope == "overall"]
    channel_rankings = {
        channel: [entry for entry in rankings if entry.scope == "channel" and entry.channel == channel]
        for channel in channels
    }
    channel_counts = _channel_counts(rows)
    channel_sections = _channel_sections(channels, channel_rankings, channel_counts)
    context = {
        "report_date": report_date.isoformat(),
        "topics": topics,
        "overall": overall,
        "channels": channels,
        "channel_rankings": channel_rankings,
        "channel_sections": channel_sections,
        "items": item_map,
        "failures": failures,
        "root_prefix": ".",
    }
    overview_path = output_dir / "index.html"
    overview_path.write_text(env.get_template("overview.html").render(**context), encoding="utf-8")

    data = {
        "date": report_date.isoformat(),
        "topics": [topic.__dict__ for topic in topics],
        "rankings": [entry.__dict__ for entry in rankings],
        "failures": failures,
    }
    (assets_dir / "report-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return overview_path


def _row_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def _channel_counts(rows: list[sqlite3.Row]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        channel = row["source_channel"]
        counts[channel] = counts.get(channel, 0) + 1
    return counts


def _channel_sections(
    channels: dict,
    channel_rankings: dict[str, list[RankingEntry]],
    channel_counts: dict[str, int],
) -> list[dict]:
    ordered_channels = [channel for channel in CHANNEL_ORDER if channel in channels]
    ordered_channels.extend(channel for channel in channels if channel not in ordered_channels)
    sections = []
    for channel in ordered_channels:
        entries = channel_rankings.get(channel, [])
        if not entries:
            continue
        total_count = max(channel_counts.get(channel, 0), len(entries))
        label = CHANNEL_LABELS.get(channel) or channels[channel].get("label", channel)
        sections.append(
            {
                "key": channel,
                "label": label,
                "code": channel,
                "description": channels[channel].get("description", _channel_description(channel)),
                "count": total_count,
                "top_entries": entries[:10],
                "extra_entries": entries[10:],
                "more_count": max(total_count - 10, 0),
            }
        )
    return sections


def _channel_description(channel: str) -> str:
    descriptions = {
        "official": "发布、产品、政策",
        "chinese_media": "国内产品、产业落地",
        "industry": "融资、商业化、生态",
        "github": "开源项目、工具链",
        "papers": "研究趋势、方法论",
    }
    return descriptions.get(channel, "来源信号")
