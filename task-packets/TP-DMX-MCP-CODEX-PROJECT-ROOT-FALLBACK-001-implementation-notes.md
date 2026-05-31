---
id: TP-DMX-MCP-CODEX-PROJECT-ROOT-FALLBACK-001-implementation-notes
title: Tp Dmx Mcp Codex Project Root Fallback 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-30'
last_review: '2026-05-30'
next_review: '2026-08-28'
prelude: Tp Dmx Mcp Codex Project Root Fallback 001 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-MCP-CODEX-PROJECT-ROOT-FALLBACK-001 Implementation Notes

## Summary

- Added a repo-owned Codex plugin distribution at `plugins/dopemux-mission-control/`.
- Added a regression test for launching the repo-owned Task Orchestrator stdio wrapper from a non-git cwd with no explicit project-root env.
- Updated `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh` so Codex session metadata cwd is a last-resort workspace root source.
- Preserved explicit env and current git cwd precedence before the Codex fallback.
- Documented the Codex fallback in `docs/02-how-to/manage-mcp-servers.md`.
- Added two CI-unblock compatibility fixes observed after PR creation: legacy UI panel aggregate adapters and explicit grandfathering for pre-existing audit proof bundles that already violate the embedded-audit schema.
- Addressed automated PR review findings for unset `HOME`, stale Docker container race handling, missing launcher test assertion, task-packet absolute allowlist paths, and legacy PR queue item mapping.

## Root Cause

Observed Codex config at `/Users/hue/.codex/config.toml` starts `task-orchestrator-current-stdio.sh` with only `PATH` in the task-orchestrator env block. When Codex starts the required MCP server from a non-project cwd, the previous launcher had no workspace root source and exited before MCP initialize.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-MCP-CODEX-PROJECT-ROOT-FALLBACK-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `python3 /Users/hue/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/dopemux-mission-control`
- PASS: pre-fix regression reproduced with `uv run --extra test pytest tests/unit/test_task_orchestrator_launcher.py -q`; failure was `could not derive workspace root from env or current git root`.
- PASS: `bash -n /Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`
- PASS: `bash -n plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh`
- PASS: post-fix `uv run --extra test pytest tests/unit/test_task_orchestrator_launcher.py -q`
- PASS: `plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution`
- PASS: `cd /tmp && /Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution`
- PASS: `/Users/hue/plugins/dopemux-mission-control/scripts/task-orchestrator-current-stdio.sh --print-resolution`
- PASS: after Codex restart, `mcp__task_orchestrator.get_context(mode="health-check", includeAncestors=true)` returned a health-check payload with 2 active items, 0 blocked items, 0 stalled items, and `claimSummary.active=0`, `claimSummary.expired=0`.
- FAIL: one-off raw JSON-RPC initialize smoke from `/tmp` returned exit code 1 and produced no JSON response; this was not accepted as proof because it was not a confirmed MCP client harness.
- PASS: removed the smoke-created stale container with `docker rm -f task-orchestrator-dopemux-mvp-2e346e2084bca021`.
- PASS: `uv run --frozen pytest tests/unit/orchestrator/test_data_sources.py tests/unit/orchestrator/test_ui_data_sources.py -q` after restoring legacy panel aggregate adapters.
- PASS: `python3 scripts/audit/validate_audit_proof.py --all proof/ --quiet` after adding explicit exclusions for six pre-existing non-compliant legacy proof bundles.
- PASS: `uv run --frozen pytest tests/unit tests/test_voice_core.py tests/test_brand_voice.py -n auto --maxfail=1 --disable-warnings --no-cov` returned `981 passed, 2 skipped, 1 warning`.
- PASS: post-review `uv run --extra test pytest tests/unit/test_task_orchestrator_launcher.py -q` returned 2 passed, including the unset-`HOME` regression path with `CODEX_HOME`.
- PASS: post-review `env -i PATH="$PATH" .../task-orchestrator-current-stdio.sh --print-resolution` returned workspace/project roots for both repo-owned and installed launchers.
- PASS: post-review `uv run --frozen pytest tests/unit/orchestrator/test_data_sources.py tests/unit/orchestrator/test_ui_data_sources.py tests/unit/pm/test_pm_route_contracts.py -q` returned 17 passed.
- PASS: post-review `uv run --frozen pytest tests/unit tests/test_voice_core.py tests/test_brand_voice.py -n auto --maxfail=1 --disable-warnings --no-cov` returned `982 passed, 2 skipped, 1 warning`.

## Residual Risk

- Existing already-started Codex MCP transports may need a thread/app restart to pick up the patched launcher. A restart was validated in this thread after the local launcher patch.
- If multiple Codex threads are starting concurrently and no env/git cwd is available, the fallback uses the newest Codex session index entry. Explicit env or git cwd remains the deterministic override.
- The proof validator exclusions unblock known historical bundles; they do not repair those legacy proof artifacts. The exclusion reasons keep that debt explicit.
