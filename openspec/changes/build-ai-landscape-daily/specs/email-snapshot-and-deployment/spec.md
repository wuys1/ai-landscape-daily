## ADDED Requirements

### Requirement: Generate email snapshot image
The system SHALL generate an email-friendly snapshot image of the daily overview.

#### Scenario: Snapshot generation succeeds
- **WHEN** static report rendering completes
- **THEN** the system uses browser automation to save a snapshot image under the daily report assets

#### Scenario: Snapshot generation fails
- **WHEN** browser automation fails to generate the snapshot
- **THEN** the system logs the error and can still generate the static report output

### Requirement: Send daily email with snapshot and report link
The system SHALL send an email containing the report date, snapshot image, and link to the static report when email sending is enabled.

#### Scenario: Email sending enabled
- **WHEN** the pipeline runs with email credentials and `--send`
- **THEN** the system sends the daily email to the configured recipient

#### Scenario: Email sending disabled
- **WHEN** the pipeline runs without `--send`
- **THEN** the system generates report files without attempting email delivery

### Requirement: Configure secrets through environment variables
The system SHALL read API keys and email credentials from environment variables rather than committed files.

#### Scenario: Required secret is missing
- **WHEN** email sending or LLM extraction requires a missing environment variable
- **THEN** the system fails with a clear configuration error for that feature

### Requirement: Run daily generation in GitHub Actions
The system SHALL include a GitHub Actions workflow that can run on a schedule and manually through workflow dispatch.

#### Scenario: Scheduled workflow runs
- **WHEN** the configured cron schedule triggers
- **THEN** GitHub Actions runs the daily generation command

#### Scenario: Manual workflow runs
- **WHEN** a user starts the workflow manually
- **THEN** GitHub Actions runs the same daily generation command

### Requirement: Publish generated static site
The system SHALL support publishing the generated `site/` directory as a static website from GitHub Actions.

#### Scenario: Static site artifact uploaded
- **WHEN** daily generation completes successfully in GitHub Actions
- **THEN** the workflow uploads the `site/` directory for static hosting deployment

### Requirement: Document setup requirements
The system SHALL document local setup, GitHub secrets, scheduled workflow behavior, and manual run instructions.

#### Scenario: User reads setup documentation
- **WHEN** a user opens the project README
- **THEN** they can identify required secrets, local commands, and GitHub Actions setup steps
