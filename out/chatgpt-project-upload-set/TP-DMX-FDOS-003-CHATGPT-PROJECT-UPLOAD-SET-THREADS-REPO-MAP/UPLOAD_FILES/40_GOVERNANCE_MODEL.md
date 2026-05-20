---
id: governance-model
title: Governance Model
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Governance rules for Task Packet execution, truth hierarchy, proof, and docs validation.
---
# Governance Model

This model summarizes current repo governance for documentation and
repo-changing work. It does not replace `AGENTS.md` or
`docs/03-reference/governance/rules.md`.

## Truth Hierarchy

Use this truth hierarchy when sources conflict:

1. Active Task Packet for scope, allowlist, validation, and stop conditions.
2. Runtime code, config, compose wiring, tests, and active entrypoints.
3. Tracked truth/reference docs under `docs/03-reference/truth/` and current
   system docs.
4. Current governance/reference docs such as `PROJECT.md`, `ARCHITECTURE.md`,
   `PM_PLANE.md`, `SERVICE_CATALOG.md`, and system references.
5. Historical, generated, archived, uploaded, exploratory, or design docs.
6. Assumptions, explicitly labeled `UNKNOWN` or `NEEDS_REPO_VERIFICATION`.

Task Packets control scoped execution. They do not make unsupported runtime
claims true.

## Task Packet Requirements

Non-trivial repo-changing work requires a generated Task Packet before
implementation. The packet must be validated against
`docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` when the schema
is available.

Each packet must declare:

- repo binding and marker
- series identity and dependency order
- branch and commit plan
- allowlisted files
- validations
- expected files
- proof obligations

Do not edit outside the packet allowlist unless a later operator instruction
explicitly changes scope.

## Worktree And Branch Discipline

Before edits:

```bash
git status -sb
git branch --show-current
git rev-parse --show-toplevel
git remote -v
```

Use a dedicated branch or worktree. Preserve unrelated dirty files. Do not
reset, clean, or overwrite user work without explicit authorization.

## Proof Rules

Proof must include:

- Task Packet ID and path
- branch and commit SHA
- PR URL or exact blocker
- files changed
- validations with exit codes
- known failures
- `UNKNOWN`s
- residual risks
- runtime checks marked `PASS`, `FAIL`, or `NOT_RUN`
- rollback plan

Proof is evidence for review. It is not a substitute for missing validation.

## Docs Validation Gates

For documentation-heavy packets, use changed-file checks before broad checks:

```bash
python scripts/docs_validator.py <changed-docs>
python scripts/docs_frontmatter_guard.py <changed-docs>
python scripts/check_root_hygiene.py
git diff --check
pre-commit run --files <changed-files>
```

When a packet requires full-repo validators, run them and record failures. If
they fail on files outside the packet allowlist, preserve that as residual docs
hygiene debt instead of silently expanding the packet.

## Completion Language

Use precise states:

- `PASS`: directly validated.
- `FAIL`: command or check failed.
- `NOT_RUN`: not executed.
- `UNKNOWN`: not proven by inspected evidence.
- `NEEDS_REPO_VERIFICATION`: plausible from docs/code but not exercised live.

Do not claim runtime drift is closed unless runtime validation actually proves
it. Do not claim a packet is accepted until proof is recorded and the operator
or reviewer accepts it.
