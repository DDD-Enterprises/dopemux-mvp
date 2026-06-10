# Serena Remediation Fix Plan

## Slice 1: Canonical Runtime Source (High Impact)
- **Objective:** Ensure the Docker runtime uses the local `services/serena` source to maintain repo-truth.
- **Allowed Files:** `docker/mcp-servers/serena/Dockerfile`
- **Action:** 
    - Remove `uv pip install git+...`
    - Add `COPY services/serena /app/services/serena`
    - Install via `uv pip install -e /app/services/serena` (or as part of root package if applicable).
- **Verification:** `docker compose build serena` followed by checking if local changes to `mcp_server.py` are reflected in the container.
- **Exit Condition:** Serena container builds and runs using local source code.

## Slice 2: Explicit Workspace Root (Medium Impact)
- **Objective:** Fix brittle workspace detection in containerized environments.
- **Allowed Files:** `services/serena/mcp_server.py`
- **Action:**
    - Modify `initialize()` and `_detect_workspace()` to check for `DOPEMUX_WORKSPACE_ROOT` or `WORKSPACE_ID` environment variables before falling back to CWD-based `.git` detection.
- **Verification:** Run Serena in Docker and verify it correctly identifies `/workspaces` (or the linked project path) as the workspace.
- **Exit Condition:** Workspace detection is deterministic and controllable via environment variables.

## Slice 3: Config and Registry Unification (Low Impact)
- **Objective:** Reduce alias sprawl and unify service registry.
- **Allowed Files:** `src/dopemux/claude_config.py`, `services/registry.yaml` (mark as deprecated or remove).
- **Action:**
    - Consolidate all `serena` aliases to `dopemux-serena` in `claude_config.py`.
    - Ensure `src/dopemux/mcp/registry.yaml` is the sole source of truth for MCP configurations.
- **Verification:** Verify that `dopemux` CLI still correctly routes to Serena using the unified alias.
- **Exit Condition:** One canonical alias and one authoritative registry file.

## Slice 4: Tool Invocation and File I/O Boundary Hardening
- **Objective:** Solidify the contract for internal tool calls and file access.
- **Allowed Files:** `services/serena/mcp_server.py`
- **Action:**
    - Add explicit logging for all subprocess calls.
    - Ensure `_resolve_path` handles the `/workspaces` symlink created in `start_with_info.sh` correctly.
- **Verification:** Audit logs for correct subprocess execution and successful file reads across symlinked paths.
- **Exit Condition:** All internal tool calls and file reads are logged and correctly resolved.
