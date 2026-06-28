from __future__ import annotations

from datetime import date

from ai_landscape_daily.config import load_config
from ai_landscape_daily.pipeline.generate import generate_daily


def test_mock_generation_creates_sqlite_and_static_files(tmp_path):
    result = generate_daily(
        report_date=date(2026, 6, 28),
        output_root=tmp_path / "site",
        db_path=tmp_path / "data" / "daily.sqlite3",
        config=load_config(),
        mock=True,
        send=False,
    )
    assert result.item_count >= 6
    assert result.topic_count >= 1
    assert result.overview_path.exists()
    assert (result.output_dir / "assets" / "report-data.json").exists()
    assert result.snapshot_path and result.snapshot_path.exists()
    assert list((result.output_dir / "topics").glob("*.html"))
    assert list((result.output_dir / "channels").glob("*.html"))
