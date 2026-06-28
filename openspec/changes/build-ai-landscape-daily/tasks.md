## 1. Project Setup

- [x] 1.1 Create Python package structure for collectors, pipeline, report rendering, storage, and email delivery.
- [x] 1.2 Add dependency files for runtime and development tooling.
- [x] 1.3 Add configuration files for RSS feeds, source channels, scoring weights, and local environment examples.
- [x] 1.4 Add CLI entry point for daily generation with `--date`, `--send`, and output directory options.

## 2. Storage Layer

- [x] 2.1 Implement SQLite connection and migration helpers.
- [x] 2.2 Create tables for source items, signals, topics, topic evidence, rankings, and daily reports.
- [x] 2.3 Add repository functions for inserting, updating, querying, and deduplicating source items.
- [x] 2.4 Add tests or verification script for schema creation and basic persistence.

## 3. Data Collection

- [x] 3.1 Implement RSS collector using configured feed URLs.
- [x] 3.2 Implement arXiv collector for configured AI categories.
- [x] 3.3 Implement GitHub Trending collector for AI-related repositories.
- [x] 3.4 Normalize collected items into a common item schema.
- [x] 3.5 Implement source failure handling so one failed source does not stop the full run.

## 4. Normalization and Deduplication

- [x] 4.1 Implement canonical URL normalization and tracking parameter removal.
- [x] 4.2 Implement item hash generation.
- [x] 4.3 Implement title and URL based deduplication.
- [x] 4.4 Preserve source attribution metadata for duplicate or cross-posted items.

## 5. Signal Extraction and Scoring

- [x] 5.1 Implement AI relevance filtering.
- [x] 5.2 Implement structured signal extraction for topics, entities, tags, signal type, summary, and contribution.
- [x] 5.3 Add schema validation and fallback behavior for extraction failures.
- [x] 5.4 Implement topic normalization and clustering.
- [x] 5.5 Implement explainable heat score components and final score calculation.
- [x] 5.6 Generate overall and channel-specific hotlists.

## 6. Static Web Report

- [x] 6.1 Create shared static assets and base Jinja2 layout matching the v7 visual direction.
- [x] 6.2 Render `态势总览` page with topic landscape graph, overall hotlist, and theme entry cards.
- [x] 6.3 Render `主题洞察` pages with topic switcher, supporting sources, related hotlist entries, and follow-up observations.
- [x] 6.4 Render `渠道热榜` pages with left channel list and right ranked entries containing title, tags, summary, heat score, and source link.
- [x] 6.5 Ensure all generated pages are navigable as static files without a backend server.

## 7. Email Snapshot

- [x] 7.1 Add Playwright-based snapshot generation for the daily overview page.
- [x] 7.2 Implement email HTML containing report date, snapshot image, and web report link.
- [x] 7.3 Implement email delivery through configured provider secrets.
- [x] 7.4 Ensure generation works without sending email when `--send` is omitted.

## 8. GitHub Actions and Deployment

- [x] 8.1 Add GitHub Actions workflow with scheduled and manual triggers.
- [x] 8.2 Configure workflow steps for Python setup, dependency installation, report generation, and static artifact upload.
- [x] 8.3 Document required GitHub repository secrets.
- [x] 8.4 Document GitHub Pages or static host setup.

## 9. Verification and Documentation

- [x] 9.1 Add README with local setup, generation commands, configuration, and deployment instructions.
- [x] 9.2 Add sample/mock data mode for deterministic local verification.
- [x] 9.3 Verify local generation creates SQLite data and static files under `site/`.
- [x] 9.4 Verify snapshot generation creates an image asset.
- [x] 9.5 Verify OpenSpec requirements are covered by implementation tasks before applying the change.
