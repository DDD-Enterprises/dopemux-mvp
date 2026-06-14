# Validation Report

- status: ValidationStatus.FAILED
- passed: False
- attempts: 1
- remediation_applied: True

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
- status: failed
- exit_code: 1

```text
Updated 18 file(s):
 - docs/90-adr/adr-221-event-stream-rate-limits.md
 - docs/90-adr/adr-220-dopetask-direct-health-endpoint.md
 - docs/05-audit-reports/rte-gemini-deep-pal-audit-2026-04-23.md
 - docs/05-audit-reports/rte-canonical-entrypoint-implementation-2026-04-23.md
 - docs/research/mcp-customization/README_UPLOAD_ORDER.md
 - docs/research/mcp-customization/dr-upload/05-claude-mem.md
 - docs/research/mcp-customization/dr-upload/04-claude-context.md
 - docs/research/mcp-customization/dr-upload/01-conport.md
 - docs/research/mcp-customization/dr-upload/03-serena.md
 - docs/research/mcp-customization/dr-upload/02-task-orchestrator.md
 - docs/research/mcp-customization/dr-upload/06-mem0.md
 - docs/research/mcp-customization/dr-upload/00-dopemux-context-boundaries.md
 - docs/research/mcp-customization/dr-upload/07-cross-system-synthesis.md
 - docs/research/mcp-customization/data/responsibility-collision-matrix.md
 - docs/research/mcp-customization/data/evidence-ledger.md
 - docs/archive/unclassified-top-level/implementation/pm-writes-phase1-verification.md
 - docs/archive/unclassified-top-level/implementation/pm-writes-phase1-authority-map.md
 - docs/03-reference/systems/dopemux/transport-contracts.md
```

### docs-validator
- command: `python scripts/docs_validator.py`
- status: failed
- exit_code: 1

```text
❌ 3 error(s) found:
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-221-event-stream-rate-limits.md: Invalid status 'active' for adr. Must be one of: proposed, rejected, superseded, accepted
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-221-event-stream-rate-limits.md: Invalid node_type 'adr'. Must be one of: Caveat, ADR, Milestone, Error, File, Pattern, Symbol, Decision, Task, DocPage
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-220-dopetask-direct-health-endpoint.md: Invalid status 'active' for adr. Must be one of: proposed, rejected, superseded, accepted

⚠️  67 warning(s):
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-phase-1-implementation-plan.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adrs-updated.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adrs-updated.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adrs-updated.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/template-adr-light.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-leantime-api-research.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-skeleton-light.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-221-event-stream-rate-limits.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-221-event-stream-rate-limits.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-task-orchestrator-capabilities.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-207-session-summary-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/global-mcp-configuration.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/global-mcp-configuration.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-3.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-index.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-index.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-index.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-202-serena-v2-production-validation.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-202-serena-v2-production-validation.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-220-dopetask-direct-health-endpoint.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-220-dopetask-direct-health-endpoint.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/candidate-adrs.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/candidate-adrs.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/candidate-adrs.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Context
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Decision
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/90-adr/adr-201-conport-kg-security-hardening-2.md: Missing recommended section: Consequences
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Problem
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Options
  /private/tmp/dopemux-pr-merge-537-20260501_000204/docs/91-rfc/rfc-2026-03-26-workflow-kit-transfer.md: Missing recommended section: Proposed Direction
```

## Fingerprint
- input_fingerprint: `5995b701af1cf1ddff743c9eaec42e56b1761ca5dbf81b0bd2d51335fbdbd707`
- valid_for_sha: `441c69db6acdb43db49bb1aac3fde61de3437ef7`
- created_from_state: `applied`
