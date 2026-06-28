#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" -m ai_landscape_daily generate --date 2026-06-28 --mock
test -f data/ai_daily.sqlite3
test -f site/daily/2026-06-28/index.html
test -f site/daily/2026-06-28/assets/snapshot.png
test -f site/daily/2026-06-28/assets/report-data.json
find site/daily/2026-06-28/topics -name "*.html" -maxdepth 1 | grep -q .
find site/daily/2026-06-28/channels -name "*.html" -maxdepth 1 | grep -q .
echo "Local verification passed."
