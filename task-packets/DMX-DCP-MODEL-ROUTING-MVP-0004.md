---
id: DMX-DCP-MODEL-ROUTING-MVP-0004
title: Read-Only DCP CLI Projection
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-16'
last_review: '2026-06-16'
next_review: '2026-09-14'
prelude: Read-only dopemux dcp CLI commands projecting classify_route and select_backend_policy.
---

# DMX-DCP-MODEL-ROUTING-MVP-0004 — Read-Only DCP CLI Projection

## Objective

Expose the existing pure DCP routing stack via `dopemux dcp classify` and
`dopemux dcp recommend-backend`. JSON in, JSON out. No runners, network, or writes.

## Scope IN

- `src/dopemux/commands/dcp_commands.py`
- `src/dopemux/cli.py` (register `dcp` group)
- `tests/unit/dcp/test_dcp_cli.py`
- `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0004.md`

## Scope OUT

No runner execution, Dopetask, Secure MCP, GitHub mutation, live writes, or service starts.

## Validation Summary

| Gate | Command |
|------|---------|
| compile | `python -m compileall -q src/dopemux/dcp src/dopemux/commands` |
| unit tests | `python -m pytest -q tests/unit/dcp/` |
| diff hygiene | `git diff --check` |
