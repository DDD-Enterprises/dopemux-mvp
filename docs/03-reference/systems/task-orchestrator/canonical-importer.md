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
- `--redacted-only` rejects FTS row exports and note body values that are not redaction handles.
- The output SQLite path is caller-supplied and may be under `/tmp` for dry runs.
- `--resolve-current` is explicit. Without it, no current-state materialization occurs.

## Example

```bash
python -m tools.task_orchestrator_reconcile.import_pack   --input /tmp/to-all-dbs-20260622T192814Z   --output /tmp/to-canonical-dryrun.sqlite   --archive /private/tmp/to-all-dbs-20260622T192814Z.tar.gz   --redacted-only   --resolve-current   --emit-report /tmp/to-canonical-resolve-report.json
```

## Outputs

- `source_databases`: one row per source database with classification and provenance.
- `source_work_items`, `source_dependencies`, `source_note_indexes`, `source_role_transitions`, `source_root_overviews`: safe imported source rows.
- `reconciliation_decisions`: explicit promotion/provenance decisions.
- `canonical_current_work_items`: active dopemux rows only when `--resolve-current` is set.
