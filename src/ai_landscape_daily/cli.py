from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from ai_landscape_daily.config import ROOT, load_config
from ai_landscape_daily.pipeline.generate import generate_daily


def parse_date(value: str) -> date:
    if value == "today":
        return date.today()
    return date.fromisoformat(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the AI landscape daily static report.")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="Collect data, score topics, and render a daily report.")
    generate.add_argument("--date", default="today", help="Report date as YYYY-MM-DD or 'today'.")
    generate.add_argument("--send", action="store_true", help="Send email after generation.")
    generate.add_argument("--output-dir", default=str(ROOT / "site"), help="Static site output directory.")
    generate.add_argument("--db", default=str(ROOT / "data" / "ai_daily.sqlite3"), help="SQLite database path.")
    generate.add_argument("--config-dir", default=str(ROOT / "config"), help="Configuration directory.")
    generate.add_argument("--mock", action="store_true", help="Use deterministic sample data instead of live collectors.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        result = generate_daily(
            report_date=parse_date(args.date),
            output_root=Path(args.output_dir),
            db_path=Path(args.db),
            config=load_config(Path(args.config_dir)),
            send=args.send,
            mock=args.mock,
            log=lambda message: print(f"[ai-daily] {message}", flush=True),
        )
        print(f"Generated {result.overview_path}")
        print(f"Items: {result.item_count}, topics: {result.topic_count}, rankings: {result.ranking_count}")
        if result.snapshot_path:
            print(f"Snapshot: {result.snapshot_path}")
        if result.failures:
            print(f"Source failures: {len(result.failures)}")
    return 0
