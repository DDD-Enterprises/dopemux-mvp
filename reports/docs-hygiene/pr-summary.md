---
title: Docs Hygiene Automation PR Summary
date: 2026-04-02
branch: codex/docs-hygiene-automation-system
status: draft
---

# Docs Hygiene Automation PR Summary

## Scope

This branch adds a documentation hygiene automation layer around the existing docs tooling. It does **not** perform a full-repo apply migration. It adds repo-wide audit/check support, one bounded live apply proof, and policy/reporting hardening based on real runs.

## Whole-tree Audit Totals

Source: `reports/docs-hygiene/full-tree-sweep.json`

- Docs scanned: 5,151
- Filename violations: 18
- Frontmatter updates needed: 502
- Duplicate archives proposed: 331
- Duplicate orphan-renames proposed: 47
- Duplicate manual-review cases: 15
- Placement violations: 412
- Schema errors: 502
- Schema warnings: 63
- Root hygiene violations: 0

## Bounded Live Apply Proof

Applied on:

- `docs/mobile/implementation-2.md`
- `docs/mobile/setup-2.md`

Observed result:

- orphan `-2` files were removed from the active tree
- canonical files remained at `docs/02-how-to/mobile/implementation.md` and `docs/02-how-to/mobile/setup.md`
- final frontmatter was reconciled from `type: explanation` to `type: how-to`
- no whole-tree mutation was required for the proof slice after sweep path-propagation fixes

## Manual-Review Duplicate Queue

These cases were intentionally **not** auto-archived because the duplicate checker classified them as materially different from their base file:

- `docs/03-reference/extraction/pipeline-reliability-2.md`
- `docs/03-reference/instructions/claude-3.md`
- `docs/03-reference/instructions/codex-3.md`
- `docs/03-reference/spec/dope-memory/v1/readme-3.md`
- `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md`
- `docs/05-audit-reports/audit-summary-2025-10-16-2.md`
- `docs/05-audit-reports/audit-summary-2025-10-16-3.md`
- `docs/05-audit-reports/conport-deep-status-task-extract-2026-02-06-2.md`
- `docs/05-audit-reports/conport-full-todo-coverage-matrix-2026-02-06-2.md`
- `docs/05-audit-reports/conport-live-backlog-execution-packet-2026-02-06-2.md`
- `docs/05-audit-reports/conport-master-todo-miss-matrix-2026-02-06-2.md`
- `docs/05-audit-reports/conport-underrepresented-execution-packet-2026-02-06-2.md`
- `docs/05-audit-reports/deployment-ready-summary-2.md`
- `docs/90-adr/adr-202-serena-v2-production-validation-2.md`
- `docs/90-adr/adr-202-serena-v2-production-validation-3.md`

## Artifact Policy For This PR

Committed:

- `reports/docs-hygiene/full-tree-sweep.json`
- this summary document

Not committed intentionally:

- large per-file audit artifacts such as placement/filename/duplicate detail JSON

Those can be regenerated from the branch using:

```bash
python3 scripts/docs_sweep.py --audit --audit-out reports/docs-hygiene/full-tree-sweep.json
```

## Explicit Non-Goals

- full-repo `docs_sweep.py --apply` was **not** run
- the 15 manual-review duplicate cases were **not** auto-resolved
- this branch should stay separate from the RTE pre-live / extractor integration branch
