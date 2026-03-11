# Docs Taxonomy and Index Policy

## Scope

This skill audits and reconciles active documentation only:

- Include: `docs/**/*.md`
- Exclude: `docs/archive/**`, `docs/04-explanation/history/**`

## Diataxis Placement Rules

- `tutorial` -> `docs/01-tutorials/`
- `how-to` -> `docs/02-how-to/`
- `reference` -> `docs/03-reference/` (also `docs/05-audit-reports/`, `docs/systems/`, `docs/spec/`, `docs/planes/` where applicable)
- `explanation` -> `docs/04-explanation/` (plus orchestration hubs such as `docs/planes/`, `docs/03-reference/instructions/`, and legacy `docs/instructions/`)
- `adr` -> `docs/90-adr/`
- `rfc` -> `docs/91-rfc/`
- `runbook` -> `docs/92-runbooks/`

## Canonical Indexes and Lists

Always reconcile these files for active-scope runs:

- `docs/docs_index.yaml`
- `docs/00-MASTER-INDEX.md`
- `docs/INDEX.md`
- `docs/01-tutorials/overview.md`
- `docs/02-how-to/overview.md`
- `docs/03-reference/overview.md`
- `docs/04-explanation/overview.md`
- `docs/03-reference/documentation-catalog.md`

Conditionally reconcile PM/system hubs when the impacted subsystem map includes them.
