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
    (output_dir / "topics").mkdir(exist_ok=True)
    (output_dir / "channels").mkdir(exist_ok=True)
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
    context = {
        "report_date": report_date.isoformat(),
        "topics": topics,
        "overall": overall,
        "channels": channels,
        "channel_rankings": channel_rankings,
        "items": item_map,
        "failures": failures,
        "root_prefix": ".",
    }
    overview_path = output_dir / "index.html"
    overview_path.write_text(env.get_template("overview.html").render(**context), encoding="utf-8")

    for topic in topics:
        topic_context = context | {"topic": topic, "root_prefix": ".."}
        (output_dir / "topics" / f"{topic.slug}.html").write_text(
            env.get_template("topic.html").render(**topic_context),
            encoding="utf-8",
        )

    default_channel = next(iter(channels), None)
    for channel, meta in channels.items():
        channel_context = context | {
            "selected_channel": channel,
            "selected_channel_label": meta.get("label", channel),
            "entries": channel_rankings.get(channel, []),
            "root_prefix": "..",
        }
        (output_dir / "channels" / f"{channel}.html").write_text(
            env.get_template("channel.html").render(**channel_context),
            encoding="utf-8",
        )
    if default_channel:
        shutil.copy2(output_dir / "channels" / f"{default_channel}.html", output_dir / "channels" / "index.html")

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
