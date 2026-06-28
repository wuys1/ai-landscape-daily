## ADDED Requirements

### Requirement: Collect AI source items from configured channels
The system SHALL collect AI-related source items from configured RSS feeds, GitHub Trending, and arXiv sources.

#### Scenario: Successful collection from all MVP channels
- **WHEN** the daily generation pipeline runs with valid source configuration
- **THEN** the system stores normalized items from RSS, GitHub Trending, and arXiv in SQLite

#### Scenario: One source fails
- **WHEN** one configured source fails due to timeout, invalid response, or parsing error
- **THEN** the system records the failure and continues collecting from other sources

### Requirement: Normalize and deduplicate source items
The system SHALL normalize source items into a common schema and deduplicate items by canonical URL, content hash, and title similarity.

#### Scenario: Duplicate item appears in multiple feeds
- **WHEN** the same article URL appears in more than one RSS source
- **THEN** the system stores one canonical item and preserves source attribution metadata

#### Scenario: Item has tracking parameters
- **WHEN** an item URL contains tracking parameters such as `utm_source`
- **THEN** the system removes tracking parameters before computing the canonical URL hash

### Requirement: Extract structured signals from source items
The system SHALL extract structured signals for each eligible item, including topics, entities, tags, source channel, signal type, summary, and contribution.

#### Scenario: Item is relevant to AI
- **WHEN** a collected item is classified as AI-relevant
- **THEN** the system stores extracted signal records linked to the item

#### Scenario: Item is not relevant to AI
- **WHEN** a collected item is classified as not AI-relevant
- **THEN** the system excludes the item from topic scoring and report rankings

### Requirement: Generate daily topic nodes
The system SHALL cluster item signals into daily topics with score, trend, summary, source counts, and supporting evidence.

#### Scenario: Multiple items support the same topic
- **WHEN** multiple signals refer to the same normalized topic
- **THEN** the system creates one topic node and links all supporting items to it

#### Scenario: Topic has multiple source channels
- **WHEN** a topic is supported by items from multiple channels
- **THEN** the system records channel coverage counts for that topic

### Requirement: Calculate explainable heat scores
The system SHALL calculate topic and hotlist heat scores using source weight, cross-source coverage, frequency, freshness, momentum, and community signal components.

#### Scenario: Topic score is calculated
- **WHEN** the scoring step runs for a topic
- **THEN** the system stores the final score and component values used to calculate it

#### Scenario: GitHub item contributes to community score
- **WHEN** a GitHub Trending item supports a topic
- **THEN** the system includes that item in the community signal component

### Requirement: Generate overall and channel hotlists
The system SHALL generate an overall hotlist and separate hotlists for official announcements, GitHub, papers, Chinese media, and industry/business channels.

#### Scenario: Overall hotlist is generated
- **WHEN** daily scoring completes
- **THEN** the system stores a ranked overall hotlist with title, heat score, tags, summary, and source URL

#### Scenario: Channel hotlist is generated
- **WHEN** daily scoring completes
- **THEN** the system stores channel-specific ranked lists for each configured channel
