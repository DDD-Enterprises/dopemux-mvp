# External Reference Snapshots

This directory is **read-only evidence** — copies of files that live outside the `dopemux-mvp` repo but materially affect its behavior. The originals are the source of truth; these snapshots exist so the repo history records WHEN external files changed and WHAT they looked like at that moment.

## Files

### `task-orchestrator-current-stdio.sh.snapshot-2026-05-27`

Snapshot of the task-orchestrator MCP wrapper at `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` taken after the **2026-05-27 multi-spawn fix**.

**What changed in this snapshot vs. the prior version** (backup of the pre-fix wrapper lives at `~/.local/share/dopemux-mission-control/task-orchestrator-backups/2026-05-27-multi-spawn-recovery/task-orchestrator-current-stdio.sh.original`):

- Added "Singleton enforcement (kill-and-replace)" preflight block right before `docker_args` is assembled.
- Added `--name "task-orchestrator-${workspace_id}"` to the docker run args.
- Behavior: at each invocation, the wrapper removes any container with the same name OR mounting the same `${data_dir}` before starting a fresh container. One container per workspace at a time. Opening a second Claude Code session in the same project disconnects the first.

**Why it matters**: previously every invocation spawned a new `--rm` container with no singleton lock. When Claude Code crashed without cleanly closing stdio, the container leaked. The repo had 14 task-orchestrator containers running simultaneously (4 concurrent writers against the same `dopemux-mvp-2e346e2084bca021` SQLite DB) before the fix landed.

**Original SHA-pinned image**: `ghcr.io/jpicklyk/task-orchestrator@sha256:c73e1d4688363cdc96152145a110919b25438bbe5d8ad781f7b15751eabbb670` — server version **v2.4.0**, predates v3 schema config support. The `.taskorchestrator/config.yaml` file in this repo is structurally valid v3 syntax but is silently ignored by the v2.4.0 runtime. Upgrade to **v3.x** (e.g. `:3.8.0`, digest `sha256:e47ed00aae313a85de0e6340010bfec8bdcd5f8c253d002759a4bb1ef8c122c1`) required to activate schemas.

## Update procedure

When the external wrapper changes:

1. Copy the new version into this directory with a dated filename suffix.
2. Update the corresponding section of this README explaining what changed and why.
3. Commit the snapshot + README update on a feature branch with a clear commit message.

The snapshots are not source-of-truth for runtime — they exist purely for traceability and disaster-recovery reference.
