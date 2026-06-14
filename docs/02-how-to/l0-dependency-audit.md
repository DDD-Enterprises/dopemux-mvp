---
title: L0 Dependency Audit
status: active
owner: dopemux
last_verified: 2026-06-14
id: l0-dependency-audit
type: how-to
author: '@hu3mann'
date: '2026-06-13'
last_review: '2026-06-13'
next_review: '2026-09-11'
prelude: L0 Dependency Audit (how-to) for dopemux documentation and developer workflows.
---
# L0 Dependency Audit

`templates/plugin/l0_membership.json` is the machine-readable source for the
cold-start L0 plugin membership audit.

The audit covers:

- `.claude/commands/dx/*.md`
- `.claude/hooks/*`
- `.claude/commands/research-quick.md`
- `.claude/commands/research-deep.md`
- `.claude/commands/research-report.md`
- `.claude/commands/implement.md`
- `.claude/commands/plan.md`
- `.claude/commands/plan-tasks.md`
- `.claude/commands/plan-slice.md`

## Tier Rules

`L0` means the file has no direct local fleet coupling in the inspected source:

- no `mcp__task-orchestrator__*`
- no `mcp__conport__*`
- no `localhost` or `127.0.0.1` probe
- no Docker command requirement
- no localhost `requests.get(...)`
- no `socket.create_connection(...)` or `socket.connect(...)`

`L0.5` means the file depends on one or more local services, MCP servers, Docker,
or a local port. These items are not standalone plugin members until a later
packet adds and tests an explicit hard-degrade path.

The current audit is conservative: fail-open hooks that still probe localhost or
Docker are classified as `L0.5` unless the file has no direct fleet-coupling
pattern.

## Current Result

The manifest currently records 39 surfaces:

- `L0`: 6
- `L0.5`: 33

The `L0` set is:

- `hook/dcp-denylist-nudge`
- `hook/dcp-surface-guard`
- `hook/orchestrator-post-edit-nudge`
- `hook/proof-tracking-guard`
- `command/implement`
- `command/plan-slice`

## Rerun Procedure

When a keeper command or hook changes:

1. Re-inspect the changed file for the tier rules above.
2. Update `templates/plugin/l0_membership.json` with line-specific evidence.
3. Run:

```bash
python -m json.tool templates/plugin/l0_membership.json
pytest -q tests/coldstart/test_l0_membership.py
```

If a file should move from `L0.5` to `L0`, remove or test the direct fleet
coupling first. Do not classify a file as `L0` by relying on an assumed runtime
fallback that is not enforced by `tests/coldstart/test_l0_membership.py`.
