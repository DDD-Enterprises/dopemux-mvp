# Validation Report

- status: ValidationStatus.PASSED
- passed: True
- attempts: 1
- remediation_applied: False

## Steps
### pre-commit
- command: `pre-commit run`
- status: passed
- exit_code: 0

```text
Validate YAML frontmatter in docs......................................(no files to check)Skipped
Validate documentation against knowledge graph schema..................(no files to check)Skipped
Block prohibited documentation patterns (NOTES, TODO, TEMP, etc.)......(no files to check)Skipped
Validate prelude ≤100 tokens for efficient embeddings..................(no files to check)Skipped
Enforce markdown file locations for changed files......................(no files to check)Skipped
Enforce docs placement hygiene (changed files).........................(no files to check)Skipped
Enforce docs filename hygiene (kebab-case).............................(no files to check)Skipped
Audit docs filename hygiene (kebab-case, full-tree legacy debt)............................Passed
Reject executable/config code under UPGRADES (docs-only legacy tree)...(no files to check)Skipped
Enforce repository root hygiene (no random root files).................(no files to check)Skipped
markdownlint...........................................................(no files to check)Skipped
trim trailing whitespace...............................................(no files to check)Skipped
fix end of files.......................................................(no files to check)Skipped
check yaml.............................................................(no files to check)Skipped
```

### docs-frontmatter-fix
- command: `python scripts/docs_frontmatter_guard.py --fix`
- status: passed
- exit_code: 0

```text
All docs have valid frontmatter.
```

### docs-validator
- command: `python scripts/docs_validator.py`
- status: passed
- exit_code: 0

```text
⚠️  67 warning(s):
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adrs-updated.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adrs-updated.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adrs-updated.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/template-adr-light.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-skeleton-light.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-221-event-stream-rate-limits.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-221-event-stream-rate-limits.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/global-mcp-configuration.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/global-mcp-configuration.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-index.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-index.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-index.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-202-serena-v2-production-validation.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-202-serena-v2-production-validation.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-220-dopetask-direct-health-endpoint.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-220-dopetask-direct-health-endpoint.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/candidate-adrs.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/candidate-adrs.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/candidate-adrs.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Problem
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Options
  /private/tmp/dopemux-pr-merge-548-20260501_001012/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Proposed Direction
```

### docs-hygiene
- command: `python scripts/check_docs_hygiene.py --check`
- status: passed
- exit_code: 0

```text
docs-hygiene: total=4851 active=3483 quarantine=1368 violations=0
docs-hygiene: OK
```

### docs-filename-hygiene
- command: `python scripts/check_docs_filename_hygiene.py --check`
- status: passed
- exit_code: 0

```text
docs-filename-hygiene: total=4851 active=3483 quarantine=1368 exempt=2156 violations=0
docs-filename-hygiene: OK
```

### root-hygiene
- command: `python scripts/check_root_hygiene.py`
- status: passed
- exit_code: 0

```text
root-hygiene: no candidate files to check
```

## Fingerprint
- input_fingerprint: `18c1a0dff192451ead47cc7621e429f088310816a05b1cc1d83dacf844a20c56`
- valid_for_sha: `f877cc1bda4fd3c28cb40a5c084b56d29c71dd2e`
- created_from_state: `applied`
