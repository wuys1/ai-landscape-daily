from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ai_landscape_daily.collectors.arxiv import ArxivCollector
from ai_landscape_daily.collectors.github import GitHubTrendingCollector
from ai_landscape_daily.collectors.rss import RSSCollector
from ai_landscape_daily.collectors.sample import SampleCollector
from ai_landscape_daily.config import RuntimeConfig
from ai_landscape_daily.email.delivery import build_email_html, send_email
from ai_landscape_daily.pipeline.extract import extract_signals
from ai_landscape_daily.pipeline.scoring import build_topics_and_rankings
from ai_landscape_daily.report.render import render_report
from ai_landscape_daily.report.snapshot import create_snapshot
from ai_landscape_daily.storage import repository
from ai_landscape_daily.storage.db import connect, migrate


@dataclass
class GenerationResult:
    report_date: date
    output_dir: Path
    overview_path: Path
    snapshot_path: Path | None
    report_url: str | None
    item_count: int
    topic_count: int
    ranking_count: int
    failures: list[tuple[str, str, str]]


def generate_daily(
    *,
    report_date: date,
    output_root: Path,
    db_path: Path,
    config: RuntimeConfig,
    send: bool = False,
    mock: bool = False,
    log: callable | None = None,
) -> GenerationResult:
    def emit(message: str) -> None:
        if log:
            log(message)

    emit(f"Opening SQLite database: {db_path}")
    conn = connect(db_path)
    migrate(conn)
    emit("SQLite schema is ready.")

    collectors = [SampleCollector()] if mock else [
        RSSCollector(config.sources.get("rss_feeds", [])),
        ArxivCollector(config.sources.get("arxiv", {})),
        GitHubTrendingCollector(config.sources.get("github_trending", {})),
    ]

    failures: list[tuple[str, str, str]] = []
    collected_item_ids: list[int] = []
    for collector in collectors:
        emit(f"Collecting source: {collector.name}")
        result = collector.collect()
        emit(f"Collected {len(result.items)} item(s) from {collector.name}; failures: {len(result.failures)}")
        failures.extend(result.failures)
        for item in result.items:
            collected_item_ids.append(repository.upsert_source_item(conn, item))
    for failure in failures:
        repository.record_failure(conn, *failure)

    rows = repository.list_items_by_ids(conn, collected_item_ids)
    emit(f"Loaded {len(rows)} item(s) from this run for extraction.")
    signals = extract_signals(rows, config.llm, log=emit)
    emit(f"Extracted {len(signals)} signal record(s).")
    repository.replace_signals(conn, signals)
    emit("Scoring topics and rankings.")
    topics, rankings = build_topics_and_rankings(rows, signals, report_date, config.scoring)
    repository.replace_topics(conn, report_date, topics)
    repository.replace_rankings(conn, report_date, rankings)
    emit(f"Generated {len(topics)} topic(s) and {len(rankings)} ranking entry records.")

    output_dir = output_root / "daily" / report_date.isoformat()
    emit(f"Rendering static report into {output_dir}")
    overview_path = render_report(
        output_dir=output_dir,
        report_date=report_date,
        rows=rows,
        topics=topics,
        rankings=rankings,
        channels=config.sources.get("channels", {}),
        failures=failures,
    )

    emit("Generating overview snapshot.")
    snapshot_path = create_snapshot(overview_path, output_dir / "assets" / "snapshot.png")
    report_url = _report_url(report_date)
    repository.save_report(
        conn,
        report_date,
        str(output_dir),
        str(overview_path),
        str(snapshot_path) if snapshot_path else None,
        report_url,
        {"failures": failures, "mock": mock},
    )

    if send:
        emit("Sending email.")
        html = build_email_html(report_date=report_date, report_url=report_url, snapshot_path=snapshot_path)
        send_email(subject=f"AI 态势日报 {report_date.isoformat()}", html=html, snapshot_path=snapshot_path)
        emit("Email sent.")

    return GenerationResult(
        report_date=report_date,
        output_dir=output_dir,
        overview_path=overview_path,
        snapshot_path=snapshot_path,
        report_url=report_url,
        item_count=len(rows),
        topic_count=len(topics),
        ranking_count=len(rankings),
        failures=failures,
    )


def _report_url(report_date: date) -> str | None:
    import os

    base = os.getenv("REPORT_BASE_URL", "").rstrip("/")
    if not base:
        return None
    if base.endswith(report_date.isoformat()):
        return base + "/"
    return f"{base}/daily/{report_date.isoformat()}/"
