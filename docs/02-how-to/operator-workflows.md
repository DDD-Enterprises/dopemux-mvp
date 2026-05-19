---
id: operator-workflows
title: Operator Workflows
type: how-to
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Operator workflows for Dopemux startup, PM routing, documentation packets, and proof.
---
# Operator Workflows

This guide gives practical operator paths without changing authority boundaries.

## Start From Repo Preflight

```bash
git status -sb
git branch --show-current
git rev-parse --show-toplevel
test -f pyproject.toml
test -f AGENTS.md
```

For service work, also inspect:

```bash
docker compose -f compose.yml config >/dev/null
python scripts/check_root_hygiene.py
```

## Operator Startup

Use `dopemux start` for the operator CLI/cockpit path:

```bash
dopemux start
```

Use explicit compose startup when you need the compose service stack:

```bash
docker network inspect dopemux-network >/dev/null 2>&1 \
  || docker network create dopemux-network
docker compose -f compose.yml up -d --build
```

Packet 003 did not run live compose startup. Mark live health as `NOT_RUN`
unless you actually run the checks.

## PM Write Routing

Classify the PM write before choosing a tool:

| PM write | Canonical writer | Rule |
| --- | --- | --- |
| title, description, assignee, passive metadata | Leantime | Do not route workflow changes through metadata writes. |
| status, phase, blocker, queue, next action | task-orchestrator | Use workflow transition surfaces. |
| decision, progress, project context | ConPort | Mirror to dope-memory only as receipt/history. |
| historical receipt | dope-memory | Do not treat receipt as current PM state. |

dopecon-bridge can proxy selected PM or KG-like calls. It is not the canonical
writer. Name the upstream authority in proof.

## Documentation Packet Flow

1. Confirm parent packet is terminal.
2. Start the next Task Packet in Task Orchestrator.
3. Create the generated packet JSON first.
4. Validate packet JSON against the canonical schema.
5. Edit only allowlisted files.
6. Run targeted validators after each meaningful slice.
7. Run required packet validators.
8. Commit only allowlisted files.
9. Open a draft PR.
10. Record proof and residual risks.

Use a dedicated branch or worktree. Do not start a child packet until the parent
packet is accepted with proof.

## Runtime And Retrieval Workflow

When using dope-context or ConPort retrieval:

1. Treat the result as derived context.
2. Open the source files or runtime code it points to.
3. Verify the claim against source, tests, compose, or active entrypoints.
4. Mark unresolved behavior as `UNKNOWN` or `NEEDS_REPO_VERIFICATION`.

## Proof Workflow

Proof should include:

- files changed
- validations with exit codes
- remote CI status when available
- full-repo validator failures, even when outside scope
- `UNKNOWN`s and residual risks
- runtime checks as `PASS`, `FAIL`, or `NOT_RUN`
- rollback plan

Do not invent results. Do not treat green docs checks as proof of runtime
correctness.
