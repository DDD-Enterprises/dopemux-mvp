---
id: PCP-GENERIC-EXPORTER
title: Generic PCP Exporter
type: how-to
owner: '@hu3mann'
author: claude
date: '2026-06-20'
last_review: '2026-06-20'
next_review: '2026-09-18'
prelude: Generic PCP Exporter (explanation) for dopemux documentation and developer
  workflows.
---
# Generic PCP Exporter

## What It Does

`pcp export` is a read-only runtime command that inspects an arbitrary Git
repository and emits a JSON *project control plane evidence export*.

The export validates against
`schemas/project_control_plane/project_evidence_export.schema.json` and
always sets `generated_from_fixture=false` with a real `repo_state.head_sha`
captured from the target repository.

The exporter works on any Git repository with at least one commit. It does
**not** require Dopemux, dNh CRM, Dopetask, or any other named system to be
present.

## Constraints

- **Read-only.** The exporter never writes to the target repository, makes no
  network calls, and mutates no external state.
  `forbidden_action_confirmation` in the output confirms this for each
  category of forbidden action.
- **Git only.** The target directory must be an initialised Git repository
  with at least one commit. Running against a plain directory or an empty repo
  (no commits) raises an error.
- **No named systems required.** For a plain repo with no Dopemux integration,
  `active_packet`, `status_ledger`, `proof_manifest`, and `pr_review_state`
  all report `ABSENT`. Unknown fields are recorded in the `unknowns` array
  with `result: "UNKNOWN"`.

## Usage

Run from the Python module entry point:

```bash
# Inspect the current directory
python -m dopemux.pcp.cli export

# Inspect a specific repo
python -m dopemux.pcp.cli export --repo /path/to/repo

# Write output to a file
python -m dopemux.pcp.cli export --repo /path/to/repo --output evidence.json

# Control indentation
python -m dopemux.pcp.cli export --indent 4

# Show all options
python -m dopemux.pcp.cli export --help
```

Or import the Python API directly:

```python
from dopemux.pcp.exporter import export_evidence

evidence = export_evidence("/path/to/repo")
print(evidence["repo_state"]["head_sha"])
```

## Output Contract

| Field | Value for a plain generic repo |
|---|---|
| `schema_version` | `"pcp.project_evidence_export.v0"` |
| `generated_from_fixture` | `false` (always) |
| `repo_state.head_sha` | Real 40-hex SHA from `git rev-parse HEAD` |
| `repo_state.worktree_state` | `"CLEAN"` or `"DIRTY"` |
| `repo_state.branch` | Branch name, or `null` for detached HEAD |
| `active_packet.state` | `"ABSENT"` |
| `status_ledger.state` | `"ABSENT"` |
| `proof_manifest.state` | `"ABSENT"` |
| `proof_manifest.freshness` | `"UNKNOWN"` |
| `pr_review_state.state` | `"ABSENT"` |
| `forbidden_action_confirmation.*` | All `false` |

The `unknowns` array records every field the generic exporter cannot determine,
with `result: "UNKNOWN"`.

Every produced export is validated against the schema before being returned.
If validation fails the call raises `jsonschema.ValidationError` (this is a
defensive guard that should not trigger in normal operation).

## Error Cases

- Non-git directory or `git` unavailable → `ValueError` with a clear message.
- Git repo with no commits → `ValueError` (a real `head_sha` cannot be captured).

## Running the Tests

```bash
python -m pytest -q tests/project_control_plane/test_generic_exporter.py
```

Tests are skipped gracefully when `git` is unavailable on the host.
