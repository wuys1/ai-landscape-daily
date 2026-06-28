## Context

The project is starting from an empty repository with an approved v7 product direction in Figma. The desired product is a web-first AI landscape daily that answers three questions:

- What is the current AI field landscape?
- Which events are hot overall?
- Which topics and channels explain those signals?

The first implementation will be a scheduled static-site generator rather than a continuously running web service. The system will collect RSS, GitHub Trending, and arXiv data; store normalized records in SQLite; compute topics and hotlists; render static pages; generate an email snapshot; and publish the static output through GitHub Actions.

## Goals / Non-Goals

**Goals:**

- Build a daily generation pipeline that can run locally and in GitHub Actions.
- Generate the v7 web experience:
  - `态势总览`
  - `主题洞察`
  - `渠道热榜`
- Preserve source traceability from topics and hotlist entries back to original URLs.
- Store source items, extracted signals, topics, rankings, and report metadata in SQLite.
- Send an email containing a snapshot image and a link to the generated web report.
- Keep deployment operationally simple with static output.

**Non-Goals:**

- No user accounts, personalization, saved reading lists, or authentication in the first release.
- No always-on backend server in the first release.
- No real-time refresh; the report is generated on a schedule.
- No complex graph database; topic graph data is stored as ordinary relational records and JSON fields.
- No full mobile web application; phone email receives a snapshot image and link.

## Decisions

### Decision: Use a scheduled static-site generator for MVP

The system will run as a Python CLI command, for example:

```bash
python -m ai_daily generate --date today --send
```

It will produce static files under `site/`, which can be deployed by GitHub Pages or another static host.

Alternatives considered:

- **FastAPI + database-backed web app**: more flexible, but adds hosting, uptime, auth, and operational complexity before the product shape is proven.
- **No web output, email-only**: simpler, but cannot support topic drilldown and channel exploration well.

Rationale: The product is daily and batch-oriented. Static generation is enough for the first release and keeps maintenance low.

### Decision: Treat topics as first-class objects and source items as evidence

Collected items are not only rendered as news. They are normalized into signals and clustered into topics. The topic drives the landscape graph and topic insight pages; source items explain why the topic exists.

Core entities:

- `items`: raw normalized source entries.
- `signals`: extracted topics, entities, tags, signal type, and importance.
- `topics`: daily topic nodes with score, trend, summary, and graph metadata.
- `topic_items`: evidence linking source items to topics.
- `rankings`: overall and channel-specific hotlists.
- `daily_reports`: generated report metadata and output paths.

Alternatives considered:

- **Render top news directly**: easier, but loses the “landscape” product value.
- **Use a graph database**: useful later, but unnecessary for MVP.

### Decision: Use deterministic scoring plus LLM-assisted extraction

LLM calls will produce structured extraction output: topics, entities, tags, summary, signal type, and contribution. Final heat scores will use a transparent formula:

```text
heat_score =
  source_weight * 0.25
+ cross_source_score * 0.20
+ frequency_score * 0.15
+ freshness_score * 0.15
+ momentum_score * 0.15
+ community_score * 0.10
```

Alternatives considered:

- **LLM-only ranking**: faster to prototype, but hard to explain and hard to debug.
- **Rules-only classification**: cheaper, but lower quality for topic grouping and evidence summaries.

Rationale: The product needs both editorial quality and explainability.

### Decision: Render report pages with Jinja2 and client-side graph rendering

Jinja2 will render static HTML pages. The topic graph can be rendered using D3.js or Cytoscape.js from embedded JSON data. MVP can start with SVG/HTML graph output if client-side graph rendering adds too much complexity.

Report paths:

```text
site/
  daily/
    YYYY-MM-DD/
      index.html
      topics/
        <topic-slug>.html
      channels/
        <channel-slug>.html
      assets/
        snapshot.png
        report-data.json
```

### Decision: Send snapshot email, not full interactive email

The email will include:

- report title and date,
- a generated snapshot image,
- a link to the static web report.

Rationale: Email clients are inconsistent and unsuitable for interactive graph exploration. The web report is the canonical experience.

### Decision: Use GitHub Actions for first scheduled deployment

The initial deployment target is GitHub Actions plus static pages. Secrets will be configured in GitHub repository settings.

Required secrets:

- `OPENAI_API_KEY` or configured LLM provider key.
- `EMAIL_TO`.
- `EMAIL_FROM`.
- `RESEND_API_KEY` or SMTP secrets.
- Optional static hosting tokens if not using GitHub Pages.

## Risks / Trade-offs

- **RSS and website formats may change** → Keep collectors isolated by source type and continue report generation if one source fails.
- **LLM output may be inconsistent** → Require JSON schema validation, retries, and fallback summaries.
- **Topic clustering may be noisy early on** → Use controlled topic aliases and source weights, then refine after daily samples.
- **GitHub Actions scheduled runs can be delayed** → Allow manual `workflow_dispatch` and local generation.
- **SQLite history in CI may not persist by default** → Store the database as an artifact or commit generated historical metadata only when explicitly configured.
- **Static pages cannot support personalized interactions** → Accept for MVP; upgrade to a backend later if personalization becomes necessary.

## Migration Plan

1. Implement local CLI generation with sample/mock data and SQLite.
2. Add live collectors for RSS, GitHub Trending, and arXiv.
3. Render static web report pages under `site/`.
4. Generate Playwright snapshot image.
5. Add email delivery with environment-based secrets.
6. Add GitHub Actions workflow and static deployment.
7. Run manually with `workflow_dispatch` before enabling the daily schedule.

Rollback is straightforward: generated static output can be deleted or replaced by the previous report; no persistent external service migration is required for MVP.

## Open Questions

- Which LLM provider should be used first for extraction and summarization?
- Should the first static host be GitHub Pages or Cloudflare Pages?
- Which email provider should be used first: Resend or SMTP?
- Should historical SQLite data be committed, uploaded as an artifact, or stored in external object storage?
