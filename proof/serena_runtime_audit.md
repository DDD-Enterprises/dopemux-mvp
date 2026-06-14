# Serena Runtime, File I/O, and Tool Invocation Audit

## 1. Canonicality Verdict
**Verdict:** `SPLIT`

The Serena runtime authority is split between a Docker-based deployment (primary) and an in-repo source copy in `services/serena`. While the Docker build claims to install Serena from an external Git repository, it also copies several wrapper scripts from the local `docker/mcp-servers-source/serena` directory.

## 2. Actual Runtime and Deployment Paths
- **Runtime Path (Container):** `/app` inside the `serena` service defined in `compose.yml`.
- **Deployment Path (Host):** `./docker/mcp-servers/serena` (Build Context) and `./docker/mcp-servers-source/serena` (Source Wrappers).
- **In-Repo Source (Duplicate?):** `services/serena` (appears to be a copy of the logic but is not directly used by the primary Docker runtime unless the external Git repo is identical to this directory).

## 3. Read Path Map
- **Mechanism:** Direct filesystem reads via `pathlib.Path.read_text()` and `rglob`.
- **Root Resolution:**
    - Resolves against `self.workspace`.
    - `self.workspace` is detected by looking for `.git` upwards from `Path.cwd()` or defaults to `Path.cwd()`.
    - In Docker, `Path.cwd()` is typically `/app`, but volumes link host projects to `/workspaces`.
- **Security Gates:**
    - `_resolve_path` uses `full_path.relative_to(self.workspace)` to ensure the path is within the workspace boundaries.

## 4. Write Path Map
- **Mechanism:** `NONE`
- Serena (as found in `services/serena/mcp_server.py`) does not implement any write or edit tools. It is a read-only intelligence engine.

## 5. Tool Invocation Map
- **Internal Tools:**
    - `pylsp`: Invoked as a subprocess for Language Server Protocol features.
    - `find`: Invoked via shell (`find ... | wc -l`) for quick file counting.
- **Proxies:**
    - `mcp-proxy`: The main `wrapper.py` in Docker runs `mcp-proxy` to wrap the `serena` command with an SSE transport.

## 6. Alias and Config Map
- **Aliases:** `serena`, `serena-v2`, `dopemux-serena`.
- **Source of Truth:** `src/dopemux/mcp/registry.yaml` (Dopemux Registry).
- **Integration Points:**
    - `mcp-proxy-config.json`: Points to `http://127.0.0.1:3006/sse`.
    - `src/dopemux/claude_config.py`: Maps `serena` and `serena-v2` to `dopemux-serena`.
    - `services/registry.yaml`: (Legacy/Service Registry) defines port 3006.

## 7. Operator Wiring Map
- **Discovery:** `dopemux` discovers Serena via `src/dopemux/mcp/registry.yaml`.
- **Startup:** Managed via `docker compose up serena`.
- **Communication:** Operators talk to Serena through `mcp-proxy` (SSE) on port 3006.

## 8. Contradiction Table
| Issue | Severity | Description | Evidence |
| :--- | :--- | :--- | :--- |
| **Runtime Source** | High | Docker installs from external Git (`git+https://github.com/oraios/serena.git`) while local `services/serena` exists. | `docker/mcp-servers/serena/Dockerfile` vs `services/serena` |
| **Path Resolution** | Medium | Docker links host paths to `/workspaces` but Serena `_detect_workspace` looks for `.git` from CWD. | `start_with_info.sh` vs `mcp_server.py` |
| **Config Redundancy** | Low | Multiple aliases (`serena`, `serena-v2`) and registries (`services/registry.yaml` vs `src/dopemux/mcp/registry.yaml`) | `claude_config.py`, `registry.yaml` |

## 9. Dead / Stale Path Table
| Path | Status | Rationale |
| :--- | :--- | :--- |
| `services/serena` | `POTENTIALLY STALE` | May diverge from the external Git repo used in Docker. |
| `services/registry.yaml` | `LEGACY` | Superseded by `src/dopemux/mcp/registry.yaml` in newer flows. |
| `docs/archive/empty-stubs/serena-v2-deployment.md` | `STALE` | Archive path. |

## 10. Top Risks
1. **Source Drift:** Changes made to `services/serena` in the local repo are NOT reflected in the Docker runtime because the Dockerfile pulls from a remote Git URL.
2. **Workspace Mapping Failure:** If `WORKSPACE_ID` is not correctly passed or if the `.git` detection fails in the container, Serena may default to `/app` instead of the actual code.
3. **Insecure Path Resolution:** While `relative_to` is used, the use of `Path.cwd()` in a container environment can be brittle if not explicitly anchored.

## 11. Fix Recommendations
1. **Canonicalize Source:** Update `Dockerfile` to install Serena from the local `services/serena` directory instead of an external Git URL to ensure repo-truth.
2. **Explicit Workspace Root:** Modify `mcp_server.py` to prioritize an environment variable (e.g., `DOPEMUX_WORKSPACE_ROOT`) over CWD-based `.git` detection.
3. **Registry Unification:** Deprecate `services/registry.yaml` in favor of `src/dopemux/mcp/registry.yaml`.
