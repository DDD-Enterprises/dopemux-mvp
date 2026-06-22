---
id: canonical-importer
title: Canonical Importer
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Canonical Importer (reference) for dopemux documentation and developer workflows.
---
# Task Orchestrator Canonical Importer

## Purpose

`tools.task_orchestrator_reconcile.import_pack` imports a safe redacted Task Orchestrator evidence-pack directory into an offline canonical SQLite database.

## Safety Model

- Input is an extracted safe pack directory, not live database files.
- **Redaction verification is fail-safe by default (opt-out, not opt-in).** Without any flag, the importer rejects FTS row exports and note body values that are not redaction handles. The legacy `--redacted-only` flag is still accepted but is now redundant.
- `--allow-unredacted-safe-pack-input` opts out of redaction verification. It prints a loud `WARNING` to stderr and records `unredacted_opt_out: true` / `redacted_only: false` in the emitted report.
- `work_item.title` and `work_item.summary` are imported **verbatim** from the source pack; redaction covers note bodies, descriptions, metadata, and FTS rows, not titles/summaries.
- The output SQLite path is caller-supplied and may be under `/tmp` for dry runs.
- `--resolve-current` is explicit. Without it, no current-state materialization occurs.

## Reproducible Evidence

Pin `--import-run-id` and `--archive-sha256` (and rely on the deterministic manifest `generated_at_utc` = newest source mtime) so committed reports regenerate byte-stable. Without `--import-run-id` a random `to-canon-<uuid>` is generated and the evidence will not reproduce.

## Example

```bash
python -m tools.task_orchestrator_reconcile.import_pack \
  --input /tmp/to-all-dbs-20260622T192814Z \
  --output /tmp/to-canonical-dryrun.sqlite \
  --archive /private/tmp/to-all-dbs-20260622T192814Z.tar.gz \
  --archive-sha256 79e00c2ec578db0675ce9e220be423228706b2e91badbef0f31da91b33f5c3c4 \
  --import-run-id to-canon-20260622T192814Z \
  --redacted-only \
  --resolve-current \
  --emit-report /tmp/to-canonical-resolve-report.json \
  --emit-manifest /tmp/CANONICAL_DATASTORE_MANIFEST.json
```

## Outputs

- `source_databases`: one row per source database with classification and provenance.
- `source_work_items`, `source_dependencies`, `source_note_indexes`, `source_role_transitions`, `source_root_overviews`: safe imported source rows.
- `reconciliation_decisions`: explicit promotion/provenance decisions.
- `canonical_current_work_items`: active dopemux rows only when `--resolve-current` is set.
- `--emit-report` / `--emit-coldstart` / `--emit-conflicts` / `--emit-manifest`: JSON artifacts. `--emit-coldstart` conforms to `reconciliation-decision.schema.json`; `--emit-manifest` conforms to `canonical-datastore.schema.json`.
