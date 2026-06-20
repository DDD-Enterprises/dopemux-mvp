---
name: pr-docgen-sync
description: Comprehensive PR/commit documentation synchronization skill that mirrors PAL docgen's discovery-first workflow. Use when code changed in a branch/PR and you must update all impacted docs across user/developer/devops/product audiences, reconcile canonical docs indexes, enforce document-type coverage (reference/how-to/explanation with conditional tutorial and adr/rfc), run frontmatter/root-hygiene gates, and record task-orchestrator/Leantime progress with best-effort live sync plus local ledger fallback.
---

# PR Docgen Sync

Use this skill to keep documentation release-ready for `main...HEAD` changes without leaving coverage gaps.

## Inputs

Provide one normalized request:

- `baseline`: git diff baseline (default `main...HEAD`)
- `format`: `json` or `markdown` report output (default `markdown`)
- `sync_tickets`: `best-effort`, `required`, or `off` (default `best-effort`)
- `task_orchestrator_url`: optional override (default `http://localhost:8000`)
- `ticket_ids`: optional explicit IDs; if omitted, parse PM IDs from ledger
- `layout_report_path`: optional path for structured layout findings report (default `reports/docs-hygiene/pr-docgen-sync-layout-findings.json`)

## Workflow

Run all phases in order.

1. Discovery
- Resolve changed scope from `git diff --name-status <baseline>`.
- Build subsystem and audience impact map.
- Enumerate required doc targets and canonical index reconciliation set.

2. Coverage Planning
- Enforce impact matrix:
  - Required: `reference`, `how-to`, `explanation`
  - Conditional: `tutorial` only if user workflow/UX changed
  - Conditional: `adr` and `rfc` only if architecture/policy boundaries changed
- Mark missing required types as blocking findings.

3. Execution
- Update impacted docs, changelog, readme, and active LLM instruction files.
- Run docs layout audit for active docs (exclude `docs/archive/**` and `docs/04-explanation/history/**`).
- For touched/new docs, misplaced files are blocking.
- For pre-existing unrelated misplacements, emit findings to report artifacts and add PM follow-up ledger entries.

4. Ticket Progress Sync
- If `sync_tickets != off`, probe task-orchestrator health.
- Attempt live progress updates when reachable.
- Always ensure ledger fallback entries in `docs/planes/pm/task-orchestrator-leantime-followups.md`.
- If mode is `required`, fail closed when live sync fails.

5. Verification
- Run docs gates:
  - `python scripts/docs_validator.py`
  - `python scripts/docs_frontmatter_guard.py`
  - `python scripts/check_root_hygiene.py`
- Do not report completion if any required gate fails.

## Deterministic Rules

- Baseline defaults to `main...HEAD`.
- Active canonical indexes must be reconciled every run:
  - `docs/docs_index.yaml`
  - `docs/00-MASTER-INDEX.md`
  - `docs/INDEX.md`
  - `docs/01-tutorials/overview.md`
  - `docs/02-how-to/overview.md`
  - `docs/03-reference/overview.md`
  - `docs/04-explanation/overview.md`
  - `docs/03-reference/documentation-catalog.md`
- Conditionally reconcile PM/system hubs when impacted.
- Skip archive/history trees unless directly touched.
- Do not silently ignore doc placement drift.

## Output Contract

Return these sections in `json` or `markdown`:

1. `impact_map`
2. `doc_type_coverage_matrix`
3. `index_reconciliation_checklist`
4. `layout_audit`
5. `ticket_sync_results`
6. `blocking_findings`

## Bundled Scripts

- `scripts/pr_docgen_sync_workflow.py` - deterministic planning, audit, and optional ticket sync.
- `scripts/run_doc_gates.sh` - docs/frontmatter/root-hygiene validation runner.

## References

- `references/docs_taxonomy_and_index_policy.md`
- `references/pm_sync_contract.md`
