## Why

AI 信息源分散在官方公告、GitHub、论文、中文媒体和产业媒体中，普通新闻列表很难帮助用户判断“今天 AI 领域的格局是什么”。需要构建一个自动化 AI 态势日报系统，将多渠道信号聚合为态势总览、主题洞察和渠道热榜，并通过邮件提供每日入口。

## What Changes

- Add a daily data pipeline that collects AI-related items from RSS feeds, GitHub Trending, and arXiv.
- Normalize, deduplicate, classify, and score collected items into topics, overall hotlist entries, and channel-specific hotlists.
- Generate a static web report following the v7 product structure:
  - `态势总览`: topic landscape graph, overall hotlist, and theme entry cards.
  - `主题洞察`: drilldown page for a selected topic with supporting sources, related hotlist items, and follow-up observations.
  - `渠道热榜`: left-side channel switcher and right-side ranked list for the selected channel.
- Store raw items, extracted signals, topics, rankings, and generated report metadata in SQLite.
- Generate an email snapshot image plus a link to the published static report.
- Add GitHub Actions workflow support for scheduled generation and static site deployment.

## Capabilities

### New Capabilities

- `data-ingestion-and-scoring`: Collect, normalize, deduplicate, classify, cluster, and score AI information signals from RSS, GitHub Trending, and arXiv.
- `static-landscape-report`: Render the AI landscape daily web experience as static pages for overview, topic insight, and channel hotlists.
- `email-snapshot-and-deployment`: Generate an email-friendly snapshot, send the daily email, and publish static report output via GitHub Actions.

### Modified Capabilities

- None.

## Impact

- New Python project structure for collectors, pipeline logic, storage, rendering, and email delivery.
- New configuration files for feeds, channels, scoring weights, and runtime environment variables.
- New SQLite database schema for items, signals, topics, topic evidence, hotlists, and daily report metadata.
- New Jinja2 templates and static assets for the v7 web pages.
- New Playwright-based snapshot generation for email image output.
- New GitHub Actions workflow for scheduled daily generation and static site publishing.
