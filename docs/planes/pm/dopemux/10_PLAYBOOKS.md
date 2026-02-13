---
title: "Operational Playbooks"
plane: "pm"
component: "dopemux"
status: "proposed"
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
2. **Read the Logs**: Always check `logs/supervisor.log` before assuming root cause.

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
2. `dmux status` (Check identity, ports, health)
3. `dmux start`

**Long Version**:
1. Verify worktree: `cat .repo_id` matches expectation.
2. Verify git status: `git status` clean?
3. Check Limits: `dmux limits` (Are we in budget?).
4. Set Focus: `dmux focus 25m "Refactor Auth"`.
5. Start.

## Build packet fast checklist
1. **Objective**: Write one sentence goal.
2. **Context**: List 2-3 key files involved.
3. **Invariants**: What must NOT change? (e.g., "Don't break public API").
4. **Command**:
   ```bash
   dmux packet new --title "Fix Auth" --goal "JWT support" --files src/api/auth.py
   ```

## When MCP is down
**Symptom**: "Connection Refused" or "Timeout" on tool use.
**Procedure**:
1. **Detect**: `dmux health`.
2. **Restart**: `dmux restart-mcp <server_name>`.
3. **Logs**: `tail -f logs/mcp_server.log`.
4. **Degrade**: If persistent, use `dmux packet run --no-mcp` (if applicable) or switch to Manual Mode.

## When tests fail (RCA loop)
**Procedure**:
1. **Capture**: Save the failure output.
2. **Isolate**: Create a reproduction script/test case.
3. **Plan**: Generate a "Fix Packet" targeting ONLY the failure.
4. **Verify**: Run the reproduction script.
5. **No Skipping**: Do NOT ignore the test and force merge. Fix it or delete the test (if invalid).

## When limits are low (cheap-mode)
**Procedure**:
1. Switch Profile: `dmux profile set economy`.
2. Reduce Verbosity: `dmux config set output.verbose false`.
3. Increase Chunking: Break packets into smaller, atomic units to avoid long, expensive context windows.
4. Defer: Push "Nice to have" refactors to next month.

## Acceptance criteria
1. **Usability**: A new operator can follow "Start Session" and get running in < 2 minutes.
2. **Recovery**: Following "MCP Down" procedure restores service or correctly identifies a fatal error.
