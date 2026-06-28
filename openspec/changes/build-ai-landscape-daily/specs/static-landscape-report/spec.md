## ADDED Requirements

### Requirement: Render landscape overview page
The system SHALL render a static `态势总览` page for each daily report.

#### Scenario: Overview page generation
- **WHEN** report rendering runs for a date
- **THEN** the system generates `site/daily/<date>/index.html`

#### Scenario: Overview includes core sections
- **WHEN** a user opens the overview page
- **THEN** the page displays the topic landscape graph, overall hotlist, and theme entry cards

### Requirement: Render topic insight pages
The system SHALL render static `主题洞察` pages for each selected daily topic.

#### Scenario: Topic insight page generation
- **WHEN** a topic is included in the daily landscape
- **THEN** the system generates a topic page under `site/daily/<date>/topics/`

#### Scenario: Topic insight displays supporting sources
- **WHEN** a user opens a topic insight page
- **THEN** the page displays the topic summary, heat score, supporting source cards, related hotlist entries, and follow-up observations

### Requirement: Render channel hotlist pages
The system SHALL render static `渠道热榜` pages with a left-side channel list and right-side ranked entries for the selected channel.

#### Scenario: Channel hotlist page generation
- **WHEN** channel rankings exist for a daily report
- **THEN** the system generates channel pages under `site/daily/<date>/channels/`

#### Scenario: Channel page displays ranked entries
- **WHEN** a user opens a channel hotlist page
- **THEN** the page displays ranked entries with title, heat score, tags, summary, and source link

### Requirement: Link overview, topic, and channel pages
The system SHALL cross-link static pages so users can navigate between landscape overview, topic insights, and channel hotlists.

#### Scenario: User drills down from topic graph
- **WHEN** a user selects a topic node or theme entry from the overview page
- **THEN** the user can navigate to that topic's `主题洞察` page

#### Scenario: User opens a channel from navigation
- **WHEN** a user selects `渠道热榜`
- **THEN** the user can view the default channel hotlist and switch to other channel hotlists

### Requirement: Preserve source traceability in the report
The system SHALL render original source links for hotlist entries and supporting evidence.

#### Scenario: Source link rendered
- **WHEN** a source item appears in a hotlist or topic support card
- **THEN** the rendered page includes a link to the original source URL

### Requirement: Render without a running backend
The system SHALL generate pages that can be served by a static file host without a Python or Node server.

#### Scenario: Static hosting
- **WHEN** the contents of `site/` are served by GitHub Pages or another static host
- **THEN** all generated daily report pages are viewable in a browser
