---
id: repo-truth-extractor-v5-hygiene-cleanup
title: Repo Truth Extractor V5 Hygiene Cleanup
type: runbook
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-06-30'
prelude: Conservative cleanup guide for stale repo-truth-extractor run artifacts.
---
# Repo Truth Extractor v5 Hygiene Cleanup

## Purpose

Use this runbook to reduce stale extractor noise without deleting active runtime evidence or pretending live readiness changed.

## Safe to delete or quarantine

- stale `*.FAILED.*` sidecars older than their corresponding success JSON in old extractor run roots
- `.DS_Store` files under extractor outputs, docs, proof trees, and other generated debris
- `.zip` files inside old extractor run directories when they are clearly derived run artifacts
- artifacts moved by `python services/repo-truth-extractor/extraction_hygiene.py apply --apply`

## Preserve unless you have a specific reason

- current v5 run roots under `extraction/repo-truth-extractor/v5/runs/`
- telemetry snapshots, spend ledgers, and proof bundles tied to a run you still need to audit
- canonical source trees under `services/`, `src/`, `config/`, `scripts/`, and `docs/`
- any run root whose artifacts are still being reviewed or compared against a proof bundle

## Identify active versus stale run roots

- Treat run roots referenced by a current proof bundle, validator report, or ongoing operator investigation as active.
- Treat historical `v3` runs with only stale `*.FAILED.*` sidecars older than success JSON as stale archaeology, not active runtime debt.
- `blocked_promptset=true` in `RESUME_PROOF.json` is still worth reviewing before deletion because it records why resume was blocked.

## Recommended workflow

1. Run the default actionable scan:
   - `python services/repo-truth-extractor/extraction_hygiene.py scan`
2. If you need the full debris inventory, run:
   - `python services/repo-truth-extractor/extraction_hygiene.py scan --scan-mode full`
3. Review the grouped buckets:
   - `os_artifact` is mostly `.DS_Store` noise
   - `stale_resume_state` is old `*.FAILED.*` sidecar debt
   - `blocked_promptset` is low-count but potentially operator-relevant
4. Preview cleanup actions:
   - `python services/repo-truth-extractor/extraction_hygiene.py apply --dry-run`
5. Apply quarantine only after reviewing the plan:
   - `python services/repo-truth-extractor/extraction_hygiene.py apply --apply`
6. Re-run the actionable scan to confirm the remaining signal is smaller and still truthful:
   - `python services/repo-truth-extractor/extraction_hygiene.py scan`

## Interpreting preview output

`apply --dry-run` and `apply --apply` now emit a summary block alongside the planned action count.

- `eligible_actions` counts artifacts that match the current quarantine policy and would be moved.
- `skipped_blocked_promptset` counts artifacts encountered inside run roots whose `RESUME_PROOF.json` records `blocked_promptset=true`. These skips are intentional because those runs preserve operator-relevant failure context.
- `skipped_top_level_zip` counts `runs/*.zip` files that are not nested inside a run directory. These are skipped because the current policy only targets `.zip` artifacts clearly inside old run directories.
- `skipped_ambiguous` counts malformed or structurally unclear candidates, such as artifacts discovered under `runs/` without a trustworthy enclosing run directory.
- `skipped_non_matching_policy` counts inspected artifacts that do not satisfy the current quarantine policy, for example `*.FAILED.*` sidecars without a qualifying newer success artifact.

Large skip counts are not inherently a problem. They usually mean the safeguards are actively refusing artifacts that need review, do not meet policy, or do not have enough structure to quarantine safely.

## Bounded apply procedure

- Always run preview first with `--dry-run`.
- Always constrain the first real apply by both:
  - `--bucket`
  - `--limit`
- Never run an unbounded `apply --apply` on first execution against a live repo.
- For stale resume cleanup, use a narrow command such as:
  - `python services/repo-truth-extractor/extraction_hygiene.py apply --dry-run --bucket stale_resume_state --limit 20 --json`
- Before any real apply, verify:
  - `planned_actions` is at or below the intended limit
  - skip buckets are populated and believable
  - `blocked_promptset` protections are still being counted
- After a bounded apply, verify:
  - before/after stale resume deltas match the applied count
  - blocked promptset counts remain unchanged
  - no unrelated bucket moved

If the preview counts or after-state deltas do not line up exactly, stop. Do not widen scope and do not “fix forward” by running more apply.

## Expected outcome

- Default scan remains honest about total detected debris.
- Operators see grouped stale-artifact buckets instead of thousands of per-file warnings.
- Full scan remains available for forensic cleanup work.
