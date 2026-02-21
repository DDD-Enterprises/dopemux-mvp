---
title: Operational Playbooks
plane: pm
component: dopemux
status: proposed
id: 10_PLAYBOOKS
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Operational Playbooks (explanation) for dopemux documentation and developer
  workflows.
---
# Operational Playbooks

## Purpose
How to run this when tired. Standard Operating Procedures (SOPs) for the operator.

## Scope
- Routine startup/shutdown.
- Troubleshooting common failures.
- manual intervention workflows.

## Non-negotiable invariants
1. **Safety First**: When in doubt, **STOP** and backup `.dopemux/state.db`.
1. **Read the Logs**: Always check `logs/supervisor.log` before assuming root cause.

## FACT ANCHORS (Repo-derived)
- **CLI Help**: `dmux --help` (Contract).
- **Repo Preflight**: `scripts/repo_preflight.sh` (must pass effectively).
- **DopeCon Bridge**: `http://localhost:3016` (Service health check target).

## Open questions
- **Interactive Checklists**: Can we have interactive CLI ticking?
- *Resolution*: Yes, `dmux checklist start <name>` uses `rich` library to render checkboxes.

## Start session checklist
**Short Version**:
1. `cd /path/to/repo`
1. `dmux status` (Check identity, ports, health)
1. `dmux start`

**Long Version**:
1. Verify worktree: `cat .repo_id` matches expectation.
1. Verify git status: `git status` clean?
1. Check Limits: `dmux limits` (Are we in budget?).
1. Set Focus: `dmux focus 25m "Refactor Auth"`.
1. Start.

## Build packet fast checklist
1. **Objective**: Write one sentence goal.
1. **Context**: List 2-3 key files involved.
1. **Invariants**: What must NOT change? (e.g., "Don't break public API").
1. **Command**:
   ```bash
   dmux packet new --title "Fix Auth" --goal "JWT support" --files src/api/auth.py
   ```

## When MCP is down
**Symptom**: "Connection Refused" or "Timeout" on tool use.
**Procedure**:
1. **Detect**: `dmux health`.
1. **Restart**: `dmux restart-mcp <server_name>`.
1. **Logs**: `tail -f logs/mcp_server.log`.
1. **Degrade**: If persistent, use `dmux packet run --no-mcp` (if applicable) or switch to Manual Mode.

## When tests fail (RCA loop)
**Procedure**:
1. **Capture**: Save the failure output.
1. **Isolate**: Create a reproduction script/test case.
1. **Plan**: Generate a "Fix Packet" targeting ONLY the failure.
1. **Verify**: Run the reproduction script.
1. **No Skipping**: Do NOT ignore the test and force merge. Fix it or delete the test (if invalid).

## When limits are low (cheap-mode)
**Procedure**:
1. Switch Profile: `dmux profile set economy`.
1. Reduce Verbosity: `dmux config set output.verbose false`.
1. Increase Chunking: Break packets into smaller, atomic units to avoid long, expensive context windows.
1. Defer: Push "Nice to have" refactors to next month.

## Acceptance criteria
1. **Usability**: A new operator can follow "Start Session" and get running in < 2 minutes.
1. **Recovery**: Following "MCP Down" procedure restores service or correctly identifies a fatal error.
