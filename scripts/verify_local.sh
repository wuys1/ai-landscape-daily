#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" -m ai_landscape_daily generate --date 2026-06-28 --mock
test -f data/ai_daily.sqlite3
test -f site/daily/2026-06-28/index.html
test -f site/daily/2026-06-28/assets/snapshot.png
test -f site/daily/2026-06-28/assets/report-data.json
grep -q "AI日报" site/daily/2026-06-28/index.html
grep -q "官方公告" site/daily/2026-06-28/index.html
echo "Local verification passed."
