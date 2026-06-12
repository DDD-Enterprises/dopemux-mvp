# Serena-v2 Remediation Fix Plan

## Slice 1 — Fix Stale Cleanup Pattern
- **Objective:** Fix the stale reference to `serena/v2/mcp_server.py` in the PID cleanup logic.
- **Allowed Files:** `src/dopemux/cli.py`
- **Action:** Update the cleanup pattern to look for `services/serena/mcp_server.py`.
- **Verification:** Run `dopemux system status` or equivalent that triggers cleanup and verify it identifies active Serena processes correctly.

## Slice 2 — Fix Stale Setup Documentation
- **Objective:** Fix the broken path in `WORKTREE_MCP_SETUP.md`.
- **Allowed Files:** `.claude/WORKTREE_MCP_SETUP.md`
- **Action:** Update `services/serena/v2/mcp_server.py` to `services/serena/mcp_server.py`.
- **Verification:** Manually verify the path exists.

## Slice 3 — Decommission Stale Directory
- **Objective:** Remove the confusing and stale `services/serena/v2/` directory.
- **Allowed Files:** `services/serena/v2/**`
- **Action:** Delete the `services/serena/v2/` directory.
- **Verification:** Ensure the main Serena server (`mcp_server.py`) still starts and functions correctly (it should, as it does not import from this directory).

## Slice 4 — Canonize serena-v2 Identity
- **Objective:** Explicitly document `serena-v2` as the supported name for the canonical Serena service.
- **Allowed Files:** `src/dopemux/claude_config.py`
- **Action:** Add a comment explaining that `serena-v2` is the canonical name for Phase 2.
- **Verification:** Documentation check.
