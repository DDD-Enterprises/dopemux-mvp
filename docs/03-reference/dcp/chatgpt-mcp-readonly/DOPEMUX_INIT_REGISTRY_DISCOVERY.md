---
id: dcp-mcp-readonly-dopemux-init-registry-discovery
title: DCP Read-Only MCP Facade — Dopemux Init & Registry Discovery
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-05'
last_review: '2026-06-05'
next_review: '2026-09-03'
prelude: Static inspection of dopemux init and workspace-identity markers grounding the read-only MCP facade registry contract for dopemux documentation and developer workflows.
---

# Dopemux Init & Registry Discovery

> **Purpose.** TP-DCP-MCP-RO-0002 left the `dopemux init` / workspace-identity marker contract as `UNKNOWN`. This packet (TP-DCP-MCP-RO-0003) resolves it by **read-only static inspection** of the actual runtime code and repo markers, so the facade's [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md) rests on evidence, not assumption. No code, init behavior, or `.dopemux` state was modified. Every claim is labelled `OBSERVED` (verified in the working tree at the cited `file:line`), `CONFLICTING`, or `UNKNOWN`.

## 1. `dopemux init` Behavior (`OBSERVED`)

- CLI entrypoint: `src/dopemux/cli.py:725` (`def init(...)`), which imports `init_project` at `cli.py:204` and calls it at `cli.py:780`. It pre-checks for an existing workspace at `cli.py:770` (`"⚠️ Project already initialized (.dopemux/ exists)"`).
- Implementation: `src/dopemux/project_init.py` — `class ProjectInitializer` (`:33`), `self.dopemux_dir = self.workspace / ".dopemux"` (`:38`), public `init_project()` (`:265`).
- What init writes (all under the target workspace):
  - `.dopemux/` directory — `project_init.py:167` (`self.dopemux_dir.mkdir`).
  - `.dopemux/databases/` — `:168`.
  - active profile — `:171` (`self.profile_manager.set_active_profile(...)`).
  - `.dopemux/config.yaml` (optional project overrides) — `:175`.
  - It also auto-detects project type from markers (`pyproject.toml`, `package.json`, etc.) before scaffolding.

**Conclusion (`OBSERVED`):** the canonical "this workspace has been `dopemux init`-ialized" marker is the presence of the **`.dopemux/` directory**. `cli.py:770` uses exactly this check.

## 2. Workspace Identity & Detection (`OBSERVED`)

`src/dopemux/workspace_detection.py` is the canonical workspace resolver used across dopemux:

| Function | Line | Behavior |
| --- | --- | --- |
| `get_workspace_root()` | `:82` | Resolution order: `DOPEMUX_WORKSPACE_ROOT` env (`:115`) → `git rev-parse --show-toplevel` (`:135`, works for worktrees and main repo) → project markers → cwd fallback. |
| `export_workspace_env()` | `:184` | Emits `DOPEMUX_WORKSPACE_ROOT` + `DOPEMUX_WORKSPACE_ID` for MCP propagation. |
| `validate_workspace()` | `:222` | Returns `(is_valid, error_message)`; checks directory exists and is a git repo / has project markers. |
| `get_workspace_info()` | `:272` | Diagnostics: `workspace_root`, `is_git_repo`, `is_worktree`, `git_branch`, `detection_method`. |

**Conclusion (`OBSERVED`):** workspace *path* identity is git-toplevel based via `get_workspace_root()`; there is a ready-made `validate_workspace()` the facade resolver can reuse rather than re-deriving path logic.

## 3. Repo-Root / Identity Markers (`OBSERVED` + `CONFLICTING`)

Markers actually present at the repo root (existence verified; git-tracking via `git ls-files`):

| Marker | Status | Tracked | Role |
| --- | --- | --- | --- |
| `.dopemux/` | **EXISTS** (dir) | — | `dopemux init` eligibility marker (§1). |
| `.repo_id` | **EXISTS** (file) | yes | Repo identity: `project=dopemux-mvp`, `owner=hu3mann`, `intent=Primary dopemux workspace. Task packets must refuse if repo_id mismatches.` |
| `.dopetaskroot` | **EXISTS** (file) | yes | Repo-root marker used by the orchestrator. |
| `dopemux.toml` | **EXISTS** (file) | — | Project tmux/config; not an init/identity marker. |
| `.n` | **ABSENT** | — | Referenced as `repo_marker: ".n"` / `test -f .n` by several task packets (e.g. `task-packets/TP-DMX-RTECANON-001.json`, `TP-DMX-REPOHYG-003.json`) and `runbooks/BOOTSTRAP.md`, but **does not exist** in the repo. |

`CONFLICTING` — repo-marker fragmentation:
- `src/dopemux/orchestrator/operator_workflows.py:141` declares `"repo_marker": ".dopetaskroot"`.
- The DCP core schema `schemas/dcp/dcp_project_resource_map.schema.json` (from TP-DCP-0002) already canonicalizes `.repo_id` (`repo_id` field: *"Repository identifier from .repo_id marker"*) and documents `repo_root_marker` as *"Both .repo_id and dopetaskroot markers observed in repo."*
- A third marker `.n` is referenced by RTE/hygiene task packets but is **absent** — stale/aspirational drift.

**Resolution for the facade:** treat `.repo_id` as the canonical **identity** marker (consistent with the existing DCP schema authority) and `.dopemux/` as the **eligibility** marker. Do **not** silently adopt `.dopetaskroot` or `.n`; the marker fragmentation is an operator-facing `CONFLICTING` item recorded for resolution, not invented away.

**Identity consumption nuance (`OBSERVED`):** no `src/dopemux` runtime code reads `.repo_id`; it is a *declarative* identity file consumed by task-packet / DCP tooling (and asserted by `dcp_project_resource_map.schema.json`). The facade therefore reads it as data for an identity-match check, not via an existing dopemux API.

## 4. Existing Registries (`OBSERVED`)

| Registry | Location | Scope | Verdict for facade |
| --- | --- | --- | --- |
| Global workspace registry | `~/.dopemux/config.json` (`src/dopemux/global_config.py:24`; schema `default_workspace`+`workspaces{}` at `:37`; `register_workspace()` at `:93`, assigns `{name}-{hash}` slug) | **Every workspace the user has ever opened** | = **eligibility**, NOT exposure. Must not be used as the facade's exposed-project list. |
| Service registry | `services/registry.yaml` | Service ports/health (≈28 services) | Not workspaces; irrelevant to project registry. |
| MCP server registry | `src/dopemux/mcp/registry.yaml` | MCP server transport/naming | Not workspaces. |

**Conclusion (`OBSERVED`):** there is **no** `list_projects` CLI and **no** per-project exposure registry. dopemux's global registry is an "opened-workspaces" cache. This confirms TP-DCP-MCP-RO-0002 Decision **D2** (eligibility ≠ exposure): the facade must keep its **own explicit allowlist**, never auto-expose from `~/.dopemux/config.json`.

## 5. Resolved Registry/Eligibility Contract (recommendation)

Grounded in §1–§4, the facade's project resolution is:

1. **Exposure** — `project_id` must be present and `enabled: true` in the facade's own explicit registry (operator-maintained). Absent/disabled → `BLOCKED`. (Never derived from the global registry.)
2. **Eligibility validation** (fail-closed, all `OBSERVED`-backed):
   - the registered `workspace_path` resolves (canonical, symlink-followed) to a path **inside an approved root**;
   - it is a real workspace per `validate_workspace()` / `get_workspace_root()` (git toplevel);
   - it contains a **`.dopemux/`** directory (init marker, §1);
   - its **`.repo_id`** identity matches the registry entry (project/owner), per the DCP schema convention (§3).
3. Any check failing → `BLOCKED`; a partially-bound project → `PARTIAL`; never fabricated data.

This is reflected in [`MULTI_PROJECT_REGISTRY_CONTRACT.md`](MULTI_PROJECT_REGISTRY_CONTRACT.md) §4–§5.

## 6. Remaining UNKNOWNs / Open Items

- `CONFLICTING` (operator decision): canonical repo-root marker across the repo — `.repo_id` vs `.dopetaskroot` vs the absent `.n`. The facade adopts `.repo_id` for identity per the DCP schema, but repo-wide marker unification is out of scope here.
- `UNKNOWN`: whether the facade should additionally assert `.repo_id`'s `intent`/`owner` fields (beyond `project`) at resolve time — deferred to the resolver implementation in TP-DCP-MCP-RO-0004.
- `OBSERVED` drift to flag upstream (not fixed here): task packets referencing `test -f .n` / `repo_marker: ".n"` point at a non-existent marker.
