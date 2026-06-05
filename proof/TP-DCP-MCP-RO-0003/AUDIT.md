# Audit — TP-DCP-MCP-RO-0003 (Inspect Dopemux Init Registry Contract)

Auditor focus per packet `embedded_audit`. Verdict: **PASS_WITH_RISKS** (non-blocking; tracked CONFLICT + deferrals).

## 1. Were the marker findings actually observed?

Yes — every marker claim is reproduced from the working tree at a cited `file:line` (see `COMMAND_LOG.md`):
- `.dopemux/` init marker: `src/dopemux/project_init.py:167` (mkdir), checked at `src/dopemux/cli.py:770`.
- Detection: `workspace_detection.py:get_workspace_root():82`, `validate_workspace():222`, `export_workspace_env():184`.
- Markers present at root: `.repo_id` (git-tracked), `.dopetaskroot` (git-tracked), `.dopemux/` (dir), `dopemux.toml`. `.n` confirmed **ABSENT** despite task-packet references.
- `.repo_id` content read directly; `.dopetaskroot` repo_marker at `operator_workflows.py:141`; `.repo_id` canonicalized by `schemas/dcp/dcp_project_resource_map.schema.json`.

No invented markers: claims are OBSERVED, the marker fragmentation is `CONFLICTING`, residual items are `UNKNOWN`.

## 2. Did implementation accidentally begin?

No. Only two docs changed (`DOPEMUX_INIT_REGISTRY_DISCOVERY.md` created, `MULTI_PROJECT_REGISTRY_CONTRACT.md` updated) plus this proof bundle. `git diff --cached --name-only | grep src/|services/|docker/|compose` → empty. No facade code, no `.dopemux` writes, no init-behavior changes, no project auto-registration.

## 3. Does the registry contract fail closed?

Yes. The updated contract (§4/§5) requires, in order: registry presence + `enabled` → containment → `.dopemux/` eligibility + `validate_workspace()` → `.repo_id` identity match → service binding. Any miss → `BLOCKED`; partial binding → `PARTIAL`; never fabricated. Exposure is the facade's own explicit allowlist and is explicitly forbidden from being derived from dopemux's global `~/.dopemux/config.json` (which is an opened-workspaces cache = eligibility, not exposure).

## 4. Are UNKNOWNs preserved?

Yes. Two prior UNKNOWNs are marked RESOLVED with evidence; the repo-marker fragmentation is retained as a `CONFLICTING` operator item (`.repo_id` vs `.dopetaskroot` vs absent `.n`); residual `UNKNOWN`s (whether to assert `.repo_id` intent/owner beyond project at resolve time; registry file location) are routed to TP-DCP-MCP-RO-0004.

## Deviations / Residual risks (non-blocking)

- **Filename casing**: packet `allowed_files` spelled the discovery doc `Dopemux_INIT_REGISTRY_DISCOVERY.md`; used `DOPEMUX_INIT_REGISTRY_DISCOVERY.md` (ALL_CAPS) to match the dir's existing `ARCHITECTURE.md`/`MULTI_PROJECT_REGISTRY_CONTRACT.md` style and pass the repo's docs-filename-hygiene hook (mixed-case would risk rejection). Functionally identical.
- **Branch reset**: the 0003 branch was reset from the superseded stub commit `78b04fb33` onto merged main `59b309f27` so it builds on the comprehensive 0002 docs (avoids regressing 0002).
- **Upstream drift flagged (not fixed)**: task packets reference `test -f .n` / `repo_marker: ".n"` against a non-existent marker — out of facade scope, recorded for repo owners.
