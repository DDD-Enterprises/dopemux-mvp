# Serena-v2 Runtime Truth Report

## 1. Identity Verdict
**Verdict:** `SUPPORTED ALIAS`

`serena-v2` is the official internal name and a supported compatibility alias for the canonical Serena runtime (`services/serena/mcp_server.py`). It is NOT a distinct runtime. The "v2" suffix represents the current version of the system (Phase 2), but it has been merged into the root `services/serena` path.

## 2. Runtime Verdict
**Verdict:** `NOT DISTINCT`

- There is only one active Serena MCP server implementation in `services/serena/mcp_server.py`.
- This implementation initializes itself with the name `serena-v2`.
- The directory `services/serena/v2/` contains a stale or incomplete copy of the system and is NOT executed by any production path.

## 3. Deployment Verdict
**Verdict:** `UNIFIED`

- `compose.yml` defines a single `serena` service.
- Docker builds from `./docker/mcp-servers/serena`.
- `info_server.py` in the container reports the service name as `serena-v2`.

## 4. Operator Resolution Path
1. Operator uses name: `serena-v2` (or `serena`)
2. `claude_config.py` maps `serena-v2` -> `dopemux-serena`.
3. `mcp-proxy-config.json` resolves `serena` to port `3006`.
4. `docker compose` routes port `3006` to the `serena` container.
5. Container runs `mcp_server.py`, which identifies as `serena-v2`.

## 5. Config/Alias Map
| Alias | Target | Source |
| :--- | :--- | :--- |
| `serena-v2` | `dopemux-serena` | `src/dopemux/claude_config.py` |
| `serena` | `dopemux-serena` | `src/dopemux/claude_config.py` |
| `dopemux-serena` | Internal registry | `src/dopemux/mcp/registry.yaml` |

## 6. Contradiction Table
| Issue | Severity | Description | Evidence |
| :--- | :--- | :--- | :--- |
| **Stale Directory** | High | `services/serena/v2/` contains duplicated files that are older/less functional than root files. | `diff` between `adhd_features.py` files. |
| **Broken Setup Doc** | Medium | `.claude/WORKTREE_MCP_SETUP.md` refers to a non-existent `v2/mcp_server.py`. | File is missing. |
| **Cleanup Pattern** | Low | `src/dopemux/cli.py` looks for `serena/v2/mcp_server.py` for PID cleanup. | `cli.py` line 3345. |

## 7. Final Decision
**Decision:** `CANONICAL RENAMING`

- `serena`: Standardized as the **Canonical Name** for the intelligence system.
- `serena-v2`: Demoted to **Legacy Alias** for backward compatibility.
- `services/serena/v2/`: **Decommissioned and Removed** to prevent regression.
- **Runtime Guard:** Active in `mcp_server.py` to prevent "haunted path" execution.

