---
title: "Instance and Worktree Isolation"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# Instance Isolation and Workspace Identity

## Purpose
Mechanics and invariants: port offsets, workspace_id, worktree safety. Ensuring multiple Dopemux instances can run side-by-side without collision.

## Scope
- Workspace identity verification.
- Network port allocation.
- File system isolation.
- Process group isolation.

## Non-negotiable invariants
1. **Identity Binding**: A running Dopemux instance is cryptographically bound to a specific git worktree root.
2. **Port Isolation**: No two instances may share the same localhost ports for MCP or debugging.
3. **Root Lock**: An instance must refuse to run if it detects it is inside a subdirectory of another active instance's root (nested worktrees are tricky, treat with caution).

## FACT ANCHORS (Repo-derived)
- **Preflight Script**: `scripts/repo_preflight.sh`.
- **Port Manager**: `src/dopemux/net/ports.py` (to be verified).

## Open questions
- **Nested Worktrees**: How do we detect if a worktree is nested inside another?
  - *Resolution*: recursive check of parent directories for `.repo_id`.

## Worktree identity rules
- **Source**: `.repo_id` file in the root.
- **Verification**: On startup, read `.repo_id`. If missing, PROMPT user to initialize or exit.
- **Lock**: Create `.dopemux/instance.lock` containing PID and Port Offset.

## Port offset scheme
Base Ports:
- ConPort: 8000
- Context: 8001
- ...

**Offset Calculation**:
`offset = hash(absolute_path_to_root) % 100` (or manual config).
Realistically, we use a simple incremental search or a configured ID in `.dopemux/config`.

**Reserved Ranges**:
- 8000-8099: Production/Default.
- 8100-8199: Dev/Test instances.

## Per-worktree MCP isolation
- **Context Isolation**: `dopemux-context` must be configured with `data_dir = <worktree_root>/.dopemux/vectors`. It MUST NOT see vectors from other projects.
- **Tool Access**: Tools run as child processes of the Supervisor, inheriting its CWD. This naturally restricts file system access to the worktree (assuming no absolute path shenanigans).

## Cleanup and recovery
- **Safe Cleanup**:
  - `dmux stop`: Sends SIGTERM to children (MCPs), waits 5s, sends SIGKILL. Removes `.dopemux/instance.lock`.
- **Crash Recovery**:
  - If `.dopemux/instance.lock` exists but PID is dead:
    - Log "detected stale lock".
    - Remove lock.
    - Start normally.

## Failure modes
- **Port Collision**: "Address already in use".
  - *Mitigation*: Port Manager tries `base + offset`. If fail, increment offset.
- **Cross-Talk**: Instance A connects to Instance B's ConPort.
  - *Mitigation*: Auth tokens generated per-session/per-worktree in `.dopemux/secrets`.

## Acceptance criteria
1. **Multi-Run Test**: Start Dopemux in Repo A. Start Dopemux in Repo B. Both must come up online with different ports.
2. **Lock Test**: Try to start a second Dopemux in Repo A. It must refuse ("Instance already running").
