# W00 findings: Runner Memory Parity Wave 2A go / no-go

Packet: TP-DMX-RUNNERMEM2A-W00-INVESTIGATION-001 (sha256 6ff8a9751a843fad8a3b14eaaf39fdd82857b405e39a05f4f66fa36ddf0deac8, verified before work).
Worktree: /Users/hue/code/dopemux-mvp/.worktrees/runner-memory-2a, branch feat/runner-memory-2a, base 97b6d5040496e2271c41d24c339d039303bbe6b1.
Design: docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md (sha256 1fea6013...0cd3, verified). R06 hashes verified (PRE_ISSUANCE_CONPORT_PARITY.json cf7bbeed...c91, conport_parity_probe.py 8f70cdc7...b05).
Observation date: 2026-10-31. Upstream main at fetch: d9efd9f1546aa3020b54467366a215d378e8bbb3 (2026-10-29); upstream release/4.0 head: 75df163d7747d0fca9e4d050d2087d1c161366a2 (2026-10-22).
Bucket vocabulary: PASS / FAIL / NOT_RUN / UNKNOWN. Verdicts: GO / GO_REDUCED / NO_GO / UNKNOWN. advisor_calls: 0. Nothing was pulled, started, stopped, written to a keychain or called with tools/call.

## 1. Go / no-go table (read this first)

| WS | Verdict | One-line reason | Clears when |
|---|---|---|---|
| W01 dope-memory | NO_GO | `services/working-memory-assistant/**` is hard-denied by the DCP red lane (FORBIDDEN_PATHS) for any Claude Code edit and is classified `dcp_boundary` by PR Steward; CI also runs a dope-memory gate test that W01 must keep green. | Operator-approved narrow carve-out (ADR-224/226 pattern) or an explicit decision to run W01 on a non-Claude runner with the PR Steward approval. See section 13. |
| W02 ConPort | NO_GO | `docker/mcp-servers-source/conport/**` is on the same red lane. Technical design (streamable HTTP app) is sound. | Same carve-out as W01. |
| W03 `dopemux auth` | GO | New files only; no `dopemux auth` group exists; orchestrator token shape now known. Two requirements added (design changes 5, 6). | n/a |
| W04 stdio bridge | GO_REDUCED | Handshake for dope-memory and the orchestrator is verified live; the ConPort leg cannot be verified until W02 adds a streamable surface. Bridge needs a per-server profile. | W02 lands (ConPort leg only). |
| W05 orchestrator 4.0.0 | NO_GO | Upstream has no `v4.0.0` tag or release (latest `v3.16.0`); the publish workflow runs only on `v*` tags, so the 4.0.0 image is presumably unpublished. Also 4.0 removes the entire 3.x tool layer and rejects this repo's `.taskorchestrator/config.yaml`; W05's scope is far smaller than the real change. | Upstream tags and publishes 4.0.0 (digest obtainable by the operator), and the operator accepts a widened W05 or splits it (section 14). |
| W06 generator | GO_REDUCED | `--allow-sequenced` gate and 7 `full-sequenced` rows confirmed; Claude Code config comes from `mcp init`, not `generate`; gate check 2 (orchestrator token auth) cannot pass until W05 is activated. | W05 activation (gate check 2 only). |
| W07 docs and ADR | GO_REDUCED | Docs and the ADR amendment draft are buildable; "derived from committed W01 to W08" cannot be satisfied while W01, W02, W05 are NO_GO. Live Codex acceptance is NOT_RUN (operator-run). | W01, W02, W05 resolved. |
| W08 internal callers | GO_REDUCED | Of the four named files, only `pm/adapters/dope_memory.py` has an HTTP write route. `capture_client.py` and `native_hooks.py` write SQLite and Redis directly; `conport_client.py` is a mock. Fifteen other in-repo ConPort REST writers are not in W08's allowlist. `services/working-memory-assistant/conport_client.py` is also on the red lane. | Supervisor decision on the wider caller set and on G2 wording (design changes 9, 10). |

Headline findings, in order of consequence:

1. The 4.0.0 image does not demonstrably exist (section 2).
2. The red lane blocks W01 and W02 as written (section 13).
3. 4.0 removes every 3.x tool the repo's `/dx:*` commands, three hooks, `surface_manifest.json` and policy tables call; the repo's orchestrator config fails the 4.0 boot import (section 2 and section 14).
4. Orchestrator 4.0 has no log-only phase; cutover is all-or-nothing per server (section 2).
5. G2 ("every call carries a verified identity") is not achievable through bearer tokens alone: SQLite and Redis writers bypass the servers (section 11).

## 2. Q1: Task orchestrator 4.0.0 (design 5.5, 5.6, 5.10, W5)

Upstream repository: `jpicklyk/task-orchestrator`, found from the pinned reference at `scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:4` (singleton parses it at `task-orchestrator-http-singleton.sh:34-36`). Current pin: `ghcr.io/jpicklyk/task-orchestrator@sha256:e47ed00aae313a85de0e6340010bfec8bdcd5f8c253d002759a4bb1ef8c122c1`, commented v3.8.0. The running container answered `serverInfo.version 3.8.0` (probe P8).

Existence of 4.0.0 (bucket: FAIL as a release, UNKNOWN as an image):
- `gh release view v4.0.0 -R jpicklyk/task-orchestrator` returned "release not found". `gh release list` shows `v3.16.0` as Latest (2026-10-02). `gh api repos/jpicklyk/task-orchestrator/git/matching-refs/tags/v4` returned no refs; the highest tag is `v3.16.0`.
- Source says 4.0.0: `version.properties` on `main` and on `release/4.0` reads `VERSION_MAJOR=4 VERSION_MINOR=0 VERSION_PATCH=0`; `CHANGELOG.md` has `## [4.0.0] - 2026-10-17`; `server.json` has `"version": "4.0.0"` and `"identifier": "ghcr.io/jpicklyk/task-orchestrator:4.0.0"`.
- `.github/workflows/docker-publish.yml` triggers only on `push: tags: 'v*'` (lines 3-6) and pushes the image and creates the release in that run. No `v*` 4.x tag means that run has not happened. Whether a 4.0.0 image exists anyway: UNKNOWN (registry not queried; no pull allowed). The image reference documented upstream is `ghcr.io/jpicklyk/task-orchestrator:4.0.0` (fleet-deployment.md:1010). No digest is obtainable.

Auth setting (confirms and corrects the design). Source: `current/docs/fleet-deployment.md` lines 24-25, 434-440, 473-475 and `api-rest.md` lines 52-70 at main d9efd9f. URL base: https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/.
- `API_AUTH_MODE` is correct, but it only takes effect with `API_ENABLED=true`. Quoted: "`API_ENABLED=true` with `API_AUTH_MODE=bearer` or `jwks` | Credential | Every request must carry the same `Authorization: Bearer` credential" (fleet-deployment.md:24).
- `MCP_TRANSPORT=http` with the API disabled "fails startup (`MCP_AUTH`)" unless `MCP_ALLOW_UNAUTHENTICATED=true` (fleet-deployment.md:26-27 table, CHANGELOG.md:60). The current http singleton sets `MCP_TRANSPORT=http` and no `API_*` (`task-orchestrator-http-singleton.sh:187-191`), so swapping the image pin alone makes the container fail to start.
- Values: `bearer` (token file), `jwks` (JWT against a JWKS URL), `none` (needs `API_ALLOW_UNAUTHENTICATED=true`; every caller becomes the `local` principal).
- JWKS option: `API_AUTH_MODE=jwks` with `API_JWKS_URL` (https only; loopback only with `API_JWKS_ALLOW_INSECURE_URL=true`), `API_JWKS_ISSUER`, `API_JWKS_AUDIENCE`, `API_JWKS_ALGORITHMS` (fleet-deployment.md:473-486). The egress guard refuses private and Docker-network hosts (CHANGELOG.md:59, "Key fetches refuse non-public addresses"). Not suited to this single-host design.

Token file (api-rest.md:70-116):
- Path: `API_TOKENS_PATH`, default `/run/secrets/api-tokens.yaml`.
- Format: `version: 1`, then `tokens:` entries with `id` (audited as `api:<id>`), `token_sha256` ("lowercase hex SHA-256 of the plaintext token", digest must cover the exact bytes with no trailing newline), `capabilities` (list; absent or empty grants nothing), and optional `kind` (`human|agent|service`, default `service`), `profile` (`director`), `scope.root_ids`, `scope.tags_include`, `expires_at`, `description`. Any other entry key fails startup. "Token rotation requires a server restart (tokens are loaded once at startup)" (api-rest.md:116).
- Capabilities seen: `read`, `write-notes`, `write-items`, `advance`, `manage-dependencies`, `write-config`, `write-docs`, `runs`, `decide`, `admin` (fleet-deployment.md:499). Consequence: the design's "servers hold only SHA-256 hashes" is not enough for the orchestrator; each token also needs a capability set and a kind. Design change 5.

Body `actor` (CHANGELOG.md:60): "Clients stop sending `actor`: the caller is the transport principal, and a body `actor` is `unknown_parameter`." Confirmed in documentation; NOT_RUN live (no 4.0 server).

Permissive or log-only phase: none. The only relaxed modes are full-off (`API_AUTH_MODE=none` plus `API_ALLOW_UNAUTHENTICATED=true`, or `MCP_ALLOW_UNAUTHENTICATED=true` with the API disabled), where "every request is the `local` principal" (fleet-deployment.md:25-28, 513). There is no accept-and-log mode. `DEGRADED_MODE_POLICY` is removed and "a leftover variable stops the server" (CHANGELOG.md:63). The design's rollout (5.5) cannot use a `log` phase for the orchestrator.

Transport and path: Streamable HTTP at `/mcp`, `/mcp/knowledge`, `/mcp/director` on `MCP_HTTP_PORT` (image default 3001; Dockerfile `ENV MCP_HTTP_PORT=3001`; the wrapper sets it to the host port). Session id is bound to the first caller's principal (fleet-deployment.md:32). Health: `/api/v1/health` exists only with `API_ENABLED=true`; the Dockerfile health check tests a readiness file instead. A `Host` allowlist (loopback by default) runs before auth (fleet-deployment.md:42). The running 3.8.0 container answers `404` on `GET /health` (probe P7), so the 4.0 health path changes for any doctor check.

SQLite location: `DATABASE_PATH` default `data/current-tasks.db` relative to `/app` (Dockerfile line 89); the wrapper sets `DATABASE_PATH=/app/data/current-tasks.db` (`http-singleton.sh:186`, `current-stdio.sh:213`) and mounts the per-project host dir `${XDG_DATA_HOME:-$HOME/.local/share}/dopemux-mission-control/task-orchestrator/<project-id>` at `/app/data` (`current-stdio.sh:109-111`). Volume declared `VOLUME /app/data`.

3.8 to 4.0 migration (CHANGELOG.md:46, fleet-deployment.md "Upgrading from 3.x"):
- Automatic at first start (Flyway V18 to V37 plus data steps), preceded by a verified `<db>.pre-4.0.<UTC stamp>.bak` beside the database when `UPGRADE_BACKUP` is on (default). The `.bak` is on the same volume, so "keep a copy of the whole volume too".
- Irreversible in place: "a 3.x binary cannot open a V26 or later database". Rollback is restore from the `.bak` or volume copy (the doc gives the `docker run --rm -v ... alpine` commands). Verdict migration_reversible: GO_REDUCED (restore only, not in place).
- The first-start pruner deletes `call_log` rows older than 90 days, activity events older than 180 days, closed lease intervals older than 365 days unless `RETENTION_*` is set to 0 first (CHANGELOG.md:65, "The first start folds and prunes").
- `USE_FLYWAY` is ignored with a WARN; both wrappers still pass `-e USE_FLYWAY=true` (`http-singleton.sh:190`, `current-stdio.sh:215`).
- Whether this machine's 3.8.0 databases are at schema version 17 or lower: NOT_RUN (databases not opened).

Config and tool-surface breaks that W05 does not cover (design changes 1 to 4):
- `.taskorchestrator/config.yaml` in this repo (628 lines) has no `actor_authentication` block (grep: no match), so the block-removal item in Q8's premise does not apply here. It does contain 3.x forms the 4.0 boot import rejects: top-level `schemas_metadata` (not in the key-ownership table, config-reference.md:18-32), uppercase `lifecycle: AUTO|MANUAL|PERMANENT|AUTO_REOPEN` ("Enumerated values are case-sensitive and lowercase ... the removed `auto-reopen`", config-reference.md:192-194), and a top-level `traits:` registry written as bare lists. The boot import is strict: "Every other error fails startup" (config-reference.md:255-262; CHANGELOG.md:50). NOT_RUN live; evidence is the upstream docs.
- 4.0 "Every 3.x tool call shape and every 3.x REST resource route is gone" (CHANGELOG.md, "Clients and the plugin"). Removed tools include `manage_items`, `query_items`, `advance_item`, `claim_item`, `manage_notes`, `query_notes`, `manage_dependencies`, `get_context`, `get_next_item`, `get_blocked_items`, `create_work_tree`. The running server lists exactly these 14 3.x tools (probe P10).
- In this repo 24 files under `.claude/` reference those names (15 of the 18 `/dx:*` commands in `.claude/commands/dx/`, `orchestrator_enforcement.py`, `orchestrator_post_edit_nudge.py`, `orchestrator_subagent_protocol.py`, `.claude/output-styles/orchestrator.md`), plus `.taskorchestrator/surface_manifest.json`, `templates/plugin/l0_membership.json`, `mcp_tool_surfaces.json`, `src/dopemux/mcp/profile_policy.py:79-85`, `src/dopemux/pcp/task_orchestrator_projection.py:60-70`, `src/dopemux/claude/native_hooks.py:438`, and tests (`tests/orchestrator/test_dx_surface_manifest.py`, `tests/unit/orchestrator/test_operator_workflows.py`, `tests/project_control_plane/test_to_projection.py`).
- The upstream 4.0 plugin hooks "fail open" against a mismatched server, and the 3.x plugin does not work against 4.0 (CHANGELOG.md, "### Plugin").
- Principal naming: the audit id is `api:<id>`. A token with `id: runner:codex` is audited as `api:runner:codex`. The design's `runner:codex` principal needs an explicit mapping rule shared by all three servers.

Verdicts: image_ref_4_0_0 UNKNOWN; auth setting GO (with the `API_ENABLED` correction); body_actor_refused GO (doc-only); permissive_phase NO_GO; migration_reversible GO_REDUCED. W05: NO_GO.

## 3. Q2: ConPort transport (design 5.4)

R06 confirmed in source and live.
- Source: `docker/mcp-servers-source/conport/server.py` defines 17 `@mcp.tool()` functions (lines 43-215), served by `mcp.sse_app()` on `MCP_SERVER_PORT` (default 3005) only when `argv[1] == "sse"` (lines 218-229). Every tool is a thin aiohttp proxy to the REST child at `CONPORT_URL` (default `http://localhost:3004`, line 10) and sends no auth header and no instance id.
- REST `enhanced_server.py`: `POST /mcp` registered at line 276; `mcp_endpoint` at 1816 handles `tools/list` aliases, `tools/call`, and any method starting `conport_` (lines 1824-1840); anything else, including `initialize` and `notifications/initialized`, returns `-32601 "Method not found"`. `_get_tool_schemas` (line 1981) lists 13 tools, all `conport_`-prefixed (lines 1985-2151). `_dispatch_tool` (line 1858 area) maps 16 names: the 13 plus `conport_fork_instance`, `conport_promote`, `conport_promote_all`, which can be called but are not listed. The packet's R06 says REST lists 13 and SSE 17: confirmed live. Extra finding: three of the four SSE-only tools are callable through REST `tools/call` despite not being listed.
- Live (probe L1, `python3 -I conport_parity_probe.py 3019 3007`, exit 0): `rest_initialize` http 200, error -32601 "Method not found: initialize"; `rest_tools_list` count 13; `sse` "ok (server conport 1.30.0)" count 17; `identical: false`; only-SSE names: the unprefixed 17.
- Bridge side: `http_stdio_bridge.py:143-158` forwards every message, `initialize` included, unchanged. A Codex `initialize` through the bridge to the REST child therefore returns the -32601 error. The design's sentence "its REST child already answers plain JSON-RPC `POST /mcp` ... which is what the stdio bridge expects" holds for `tools/list` and `tools/call` only.

`mcp` package version in the ConPort image: the Dockerfile runs `uv pip install --system --no-cache .[services]` with no lock file (`docker/mcp-servers-source/conport/Dockerfile`), and `pyproject.toml:112` (services extra) and `:352` (override) constrain `mcp>=1.28.1,<2`. The repo lock resolves `mcp 1.29.0` (uv.lock); the running SSE surface reports `serverInfo.version 1.30.0`, consistent with the library version (inference, UNKNOWN for the exact build). FastMCP in `mcp` 1.29.0 offers `streamable_http_app()` (`.venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py:953`) beside `sse_app()` (line 821), with `json_response` and `stateless_http` settings (lines 106-107, 168-169, 963-964).

Choice: STREAMABLE_HTTP_APP (verdict GO, technically).
- It exposes the same 17 unprefixed names Claude Code sees today over SSE, so tool names stay `mcp__conport__get_context` for both runners. REST_JSONRPC would give `conport_`-prefixed names, 13 listed tools, and require adding `initialize` and `notifications/initialized` to a handler that is also the unauthenticated data plane.
- Requirement the design misses: the proxy tools in `server.py` call REST with no credentials. Whatever auth W2 puts on `:3005` must also reach `:3004` (the proxy forwards the verified principal over the docker network with a shared secret, or `:3004` stops being host-published for tool traffic). The compose and runtime publish `:3004` on host loopback (`docker_runtime.py:172-174`), so the REST data plane stays an unauthenticated write path unless it is authenticated too (design change 8).
- Adding a third surface means either a new port (registry, compose, catalog entries; PR #1485's drift test constrains it, section 12) or mounting `streamable_http_app()` under `/mcp` on the existing `:3005` Starlette app. The latter needs no new port.

Write tools. On SSE all of these write: `update_progress` (server.py:55), `log_decision` (74), `fork_instance` (117), `promote` (128), `promote_all` (135), `update_context` (151), `log_progress` (159), `save_custom_data` (189), `delete_custom_data` (202). SSE-only (not in the REST list): `fork_instance`, `promote`, `promote_all` (writes) and `workspace_summary` (read, `server.py:108`).

## 4. Q3: handshake for dope-memory and the orchestrator (probes P1 to P11)

dope-memory (`mcp_http.py:310-316`, `mcp.http_app(path="/mcp")`, FastMCP; `serverInfo` name `dope-memory` version 3.4.7, the library version):
- `initialize` must be a POST with `Accept: application/json, text/event-stream`; with `Accept: application/json` only it answers 406 "Not Acceptable: Client must accept both application/json and text/event-stream" (P5).
- The response is SSE-framed (`content-type: text/event-stream`, one `event: message` / `data: {json}` pair) and carries a `mcp-session-id` header (P2).
- `notifications/initialized` with `Mcp-Session-Id` echoed: 202, empty body (P3).
- `tools/list` with the session id: 200, SSE-framed; 10 tools: memory_search, memory_store, memory_recap, memory_mark_issue, memory_link_resolution, memory_replay_session, memory_correct, memory_generate_reflection, memory_reflections, memory_trajectory (P4).
- `tools/list` without a session id: 400 "Bad Request: Missing session ID" (P6).
- No `MCP-Protocol-Version` header was needed on later requests (P3, P4 succeeded without it).

Orchestrator 3.8.0 on :7890:
- Same Accept rule: 406 with `Accept: application/json` only (P11).
- `initialize` returns a plain `application/json` body (not SSE) plus `mcp-session-id` (P8). `serverInfo` `mcp-task-orchestrator-current` 3.8.0.
- `notifications/initialized`: 202 (P9). `tools/list`: 200, JSON body, 14 tools (P10).
- 4.0 adds `Authorization: Bearer` on every request, session binding to the principal, and `401 unauthenticated` as the 4.0 error envelope (not JSON-RPC) (fleet-deployment.md:30). 4.0 behaviour: NOT_RUN.

What W04's bridge must therefore do: send both Accept types; capture `mcp-session-id` from the `initialize` response and echo it on later requests; accept either a JSON body or an SSE `data:` frame for every response; treat 202/empty as "no response" for notifications and write nothing to stdout; stop on 401/403 with a clear stderr line; keep one session per bridge process and re-initialize on 404 (4.0 session expiry, fleet-deployment.md:32).

ConPort: see section 3 (REST has no `initialize`; SSE is a different transport). For W04 the ConPort profile is the only one that depends on W02.

## 5. Q4: stdio bridge today (`src/dopemux/mcp/http_stdio_bridge.py`)

- Forwarding: reads one JSON line from stdin (line 124), parses (134), and for every object calls `_forward_request` (145), which POSTs to `<base-url>/mcp` (line 64) with headers `Accept: application/json` and `Content-Type: application/json` only (lines 70-73). No `Authorization`, no `Mcp-Session-Id`, no SSE parsing (body is `json.loads`-ed at line 99).
- Notifications are not special-cased: a message with no `id` is still POSTed; a 202/empty reply raises `RuntimeError("Empty response body from MCP endpoint")` (95-96), which the loop converts to a JSON-RPC error with `id: null` written to stdout (146-156). That is a protocol violation toward the client.
- Timeout: default 30 s (line 23); `--timeout`, else env `DOPEMUX_MCP_BRIDGE_TIMEOUT` (47-60); mapped to `RuntimeError("Timeout contacting MCP endpoint after Ns")` (90, 93) then to `-32000 "Bridge transport error"` with `data.detail` (148-155).
- HTTP errors: `HTTP <code> from MCP endpoint: <first 400 chars of body>` (79-86); connection errors `Connection error to MCP endpoint: <reason>` (91). Parse errors `-32700`, non-object `-32600` (136-141).
- `--base-url` is required (line 111); the only in-repo user is `src/dopemux/config/manager.py:721` (docker-mode servers with `http` or `http-sse` transport pass `http://localhost:<docker.port>`), plus `tests/test_mcp_config_generation.py`.

Needed for design 5.3: (a) resolve the base URL by walking up from the working directory to `.envrc.dopemux-mcp` and reading only `*_PORT` keys with `safe_port_int` from `src/dopemux/mcp/envrc.py:217` (the file also exports a database password; `envrc.py:79` `is_secret_like_key` exists; the bridge must never load or log secret keys); (b) read the runner token from the keychain at launch and send `Authorization: Bearer` on every request; (c) fail closed: no token, no envrc, ambiguous envrc, or any 401/403 produces a stderr message and a nonzero exit, never an unauthenticated request; (d) the handshake rules in section 4; (e) notification handling; (f) fill `workspace_id` and `instance_id` into `tools/call` arguments for mutating tools from the repo identity (design 5.1) while refusing model-supplied overrides that disagree. Note a fresh worktree has no `.envrc.dopemux-mcp` (section 6 box below).

Dispatch note recorded as a finding: this worktree has no `.envrc.dopemux-mcp` (`ls .envrc*` found nothing; the file is gitignored, `.gitignore:411`). The running services (instance dcd6) belong to the main checkout, whose file defines `CONPORT_HTTP_PORT=3019`, `CONPORT_INFO_PORT=4005`, `CONPORT_MCP_PORT=3007`, `DOPE_MEMORY_PORT=3054`, `TASK_ORCHESTRATOR_HTTP_PORT=7890` (only these port lines were read). Design 5.1 and 5.3 say the bridge finds ports by walking up from the working directory. In a worktree that has not run `dopemux mcp init`, the walk finds nothing, because `.envrc.dopemux-mcp` is per checkout. Two choices for W04: fail closed with the message "run `dopemux mcp init` here" (the design's stated posture), or walk to the main checkout through `git rev-parse --git-common-dir` (which would silently bind a worktree to the main checkout's containers and defeats the workspace binding in 5.1). Recommendation: fail closed. Design change 11.

## 6. Q5: keychain (design 5.2, 5.3). Result: NOT_RUN

Nothing was created, read or deleted. Grounding is local `security help` output (no keychain access).
- `security find-generic-password -s <service> -a <account> -w` prints only the password. Usage text confirms `-w  Display only the password on stdout`.
- `security add-generic-password` usage states: "By default, the application which creates an item is trusted to access its data without warning. You can remove this default access by explicitly specifying an empty app pathname: -T """. `-T appPath` adds a trusted application; `-A` "Allow any application to access this item without warning (insecure, not recommended!)"; `-U` updates an existing item; "Use of the -p or -w options is insecure. Specify -w as the last option to be prompted."
- Inference (UNVERIFIED until the procedure runs): if `dopemux auth issue` creates the item by running `/usr/bin/security add-generic-password` with the default ACL, the trusted application is `/usr/bin/security`, so a later `subprocess.run(["/usr/bin/security", "find-generic-password", ...])` from any parent process does not prompt, provided the login keychain is unlocked. The trust is attached to the `security` binary, not to Python.

| Choice | Prompt behaviour (expected) | Risk |
|---|---|---|
| default ACL (creator `security` trusted) | no prompt while unlocked; fails or prompts when locked or in a headless context | any process of the same user can run `security find-generic-password -w` and read the token without a prompt. This matches the design's stated non-protection (section 6 of the design). |
| `-T ""` | prompt on every read | unusable for a non-interactive bridge |
| `-T <python path>` | no prompt for that interpreter | every script run by that interpreter can read the token; an interpreter path change (mise, brew upgrade) re-prompts |
| `-A` | no prompt for any application | widest exposure; also readable through Keychain APIs by any app |
| token in argv (`-w <token>`) | n/a | visible in `ps` while the command runs. Prefer `security -i` reading the command from stdin, or the `-w`-last prompt. Usage line `security [-h] [-i] ...` shows `-i` runs interactive mode. |

Operator procedure (run by the operator in a normal Terminal; the throwaway value is not a real secret):
1. Create: `security add-generic-password -s dopemux-mcp-probe -a probe -U -w` and type `test-token-1` at the prompt.
2. Non-interactive read (record the exit code and whether any dialog appeared; never print the value):
   `env -i PATH=/usr/bin:/bin /usr/bin/python3 -I -c "import subprocess,sys; r=subprocess.run(['/usr/bin/security','find-generic-password','-s','dopemux-mcp-probe','-a','probe','-w'],stdin=subprocess.DEVNULL,capture_output=True,timeout=10); print(r.returncode,len(r.stdout.strip()))"`
   Run it from: (a) the Terminal; (b) a context without a GUI session, for example `ssh localhost` or a `launchd` agent; (c) after `security lock-keychain login.keychain-db`; (d) from the Claude Code Bash tool and from the Codex shell tool. Expected for (a) if the inference holds: `0 11` (length of `test-token-1`). Record the exit codes for (b) to (d) as found.
3. Repeat step 1 with each ACL variant (`-T ""`, `-T /usr/bin/python3`, `-A`) using `-U`, and rerun step 2 to see which prompt.
4. Cleanup: `security delete-generic-password -s dopemux-mcp-probe -a probe`, then `security find-generic-password -s dopemux-mcp-probe -a probe` (no `-w`) and confirm "could not be found".
Result recording template: variant, context, exit code, dialog yes or no, date. Until this runs, keychain_noninteractive stays NOT_RUN and W03/W04 must treat "keychain locked or headless" as a hard failure with a clear message rather than a prompt.

## 7. Q6: dope-memory identity (design section 1, 5.1, W1)

Confirmed:
- `services/working-memory-assistant/dope_memory_main.py:57-58`: `DEFAULT_WORKSPACE_ID = os.getenv("DOPE_MEMORY_WORKSPACE_ID", "default")` and `DEFAULT_INSTANCE_ID = os.getenv("DOPE_MEMORY_INSTANCE_ID", "A")`. The request models default to them (`MemorySearchRequest` line 795, `MemoryStoreRequest` 812-816).
- `mcp_http.py:115-116` (`memory_store`): `workspace_id: str = default_workspace_id`, `instance_id: str = default_instance_id`; every tool does the same.
- Compose sets `DOPE_MEMORY_WORKSPACE_ID=${DOPE_MEMORY_WORKSPACE_ID:-default}` and `DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite` (`compose.yml:607-609`); per-worktree sidecars get their identity from the generated override in `src/dopemux/mcp/docker_runtime.py:185-203` (design change 7).

Mutating surfaces (DopeMemoryMCPServer methods in `dope_memory_main.py`; MCP tools in `mcp_http.py`; REST in `dope_memory_main.py`):

| Operation | Backend | MCP tool | REST route | Writes |
|---|---|---|---|---|
| memory_store | 287 (`insert_work_log_entry` 319) | mcp_http.py:110 | POST /tools/memory_store :1180 | work_log_entries |
| memory_correct | 560 (`insert_corrected_work_log_entry` 580) | :228 | POST /tools/memory_correct :1286 | work_log_entries (supersession) |
| memory_link_resolution | 452 (`insert_issue_link` 469) | :185 | POST /tools/memory_link_resolution :1246 | issue_links |
| memory_generate_reflection | 608 (`insert_reflection_card` 654) | :259 | POST /tools/memory_generate_reflection :1310 | reflection_cards |
| memory_mark_issue | 431 | :162 | POST /tools/memory_mark_issue :1225 | no write in the body (reads the entry, returns `issue_marked: true`); mutating by name only |

Read-only: memory_search (166, route :1150), memory_recap (347, :1206), memory_replay_session (482, :1266), memory_reflections (700, :1328), memory_trajectory (725, :1346; trajectory state updates happen through `upsert_trajectory_state`, `chronicle/store.py:1070`, which I did not trace to a caller from these tools: UNKNOWN).

Other writers to the same ledger that no server credential can cover: `eventbus_consumer.py:404` (`insert_raw_event`), `:431` (`insert_promoted_entry`), `:672` (`insert_reflection_card`) from the Redis stream, and `src/dopemux/memory/capture_client.py` writing SQLite directly (section 11).

Ledger path: `canonical_ledger.py` `resolve_canonical_ledger`: (1) `DOPEMUX_CAPTURE_LEDGER_PATH` wins for every workspace id, (2) workspace id as an absolute repo path, (3) walk up from `cwd`, (4) fail closed. `_get_store` keys stores by resolved path (`dope_memory_main.py:129-139`). So with the compose env set, all workspace ids share one file; W1 must stop honoring the override per request or bind the override to the container's workspace.

Schema and migrations: SQLite tables `raw_activity_events`, `work_log_entries`, `issue_links`, `reflection_cards`, `trajectory_state`, `schema_migrations` (`chronicle/schema.sql`). Migrations are `chronicle/migrations/v1_1_0 ... v1_2_1*.sql` applied by `chronicle/sqlite_migrations.py:74` through `ChronicleStore.initialize_schema()` (`chronicle/store.py:103-116`), which `_get_store` calls on first use, and which `capture_client._ensure_schema_initialized` (capture_client.py:268) also calls. So the SQLite migration is automatic on first use by either the server or any hook process, with no dry run, which differs from the ConPort posture in design 5.9. The packet and W01's allowlist name `migration_runner.py`; that file is the WMA Postgres/ConPort migration runner (`WMAMigrationRunner`, applies `wma_migration.sql`), not the chronicle SQLite migrations. Design change 6.

CI coupling: `.github/workflows/ci-complete.yml:195-199` runs `services/working-memory-assistant/tests/test_mcp_http_endpoint.py`, which calls `build_mcp_server(get_server, default_workspace_id=..., default_instance_id=...)` (test lines 44-52, 99, 139). The packet's statement that `services/*/tests` are not run by CI is false for this file. Removing the defaults changes that signature.

Verdict dope_memory_identity: GO_REDUCED (buildable as designed with changes 6, 7, 9, 10). W01 is NO_GO only because of the red lane.

## 8. Q7: ConPort identity (design 5.1, 5.9, W2)

Confirmed `docker/mcp-servers-source/conport/instance_detector.py:52-78`: `get_instance_id()` returns `os.getenv("DOPEMUX_INSTANCE_ID")`, empty string treated as unset, `None` means shared. It is one value per process: handlers call `SimpleInstanceDetector.get_instance_id()` (enhanced_server.py 507, 603, 711, 936, 1002, 1117, 1254, 1325). Per-request `instance_id` therefore needs handler changes, not only validation.

Mutating surface, REST (`enhanced_server.py` route table 245-281):
- POST /api/context/{workspace_id} (246, handler `_update_context` ~603), POST /api/decisions (249, `_log_decision` 672), POST /api/progress (253, `_log_progress` 1165), PUT /api/progress/{progress_id} (255, `_update_progress_tool` area 1254), POST /api/custom_data (270), POST /api/custom_data/claim (272), DELETE /api/custom_data (273), POST /api/instance/fork (279, `_fork_instance` 998), POST /api/progress/promote (280, 1063), POST /api/progress/promote_all (281, 1111), POST /mcp (276: `tools/call` of the 9 write tools, including the three unlisted).
- The design's list in 5.1 omits DELETE /api/custom_data, POST /api/custom_data/claim, and the three instance routes. Design change 8.
Mutating tools: REST list: conport_update_context, conport_log_decision, conport_log_progress, conport_update_progress, conport_save_custom_data, conport_delete_custom_data; unlisted but callable: conport_fork_instance, conport_promote, conport_promote_all. SSE: the 9 in section 3.

Postgres tables written and where instance lives (`schema.sql`, `migrations/007_worktree_support_simple.sql`):
- `workspace_contexts.instance_id` (schema.sql:20) and `progress_entries.instance_id` (schema.sql:71) exist.
- `decisions` has `created_by_instance` (migration 007:18) and no `instance_id`; `custom_data` has no instance column (schema.sql:109-128). So "reject a write without `instance_id`, `shared` lands where NULL lands today" has no storage meaning for decisions and custom_data; for those two it is request validation only. `entity_relationships`, `search_cache` and `session_snapshots` exist; I did not trace writes to them.

Tenant binding: compose comments describe a per-project database and LOGIN role ("credentials bind the tenant", compose.yml near line 233 onward), so the server's workspace binding in 5.1 already exists as DB credentials; the missing part is checking the request `workspace_id`.

Migration mechanism: schema bootstrap via `_ensure_schema` applies `schema.sql` with `psql` only if `workspace_contexts` is missing (enhanced_server.py:409-470), and says migrations are "operator-gated" via `/app/migrations/conport_migration_gate.py` (verify | apply; apply needs `DPMX_CONPORT_MIGRATION_APPLY=1`; ledger table `conport_schema_migrations`; `REQUIRED_MIGRATIONS` is a fixed set of five names at the top of the gate). A new migration file would be discovered (`MIGRATION_RE`) but whether `REQUIRED_MIGRATIONS` must be extended for `verify` to pass: UNKNOWN (not traced).

Deadlock: reproduced by reading source, not by running it. `apply_migrations` (gate lines 592-631) holds a psycopg2 connection (`with connect(...) as conn`) that ran `preflight_base_schema` and ledger reads without committing, then calls `run_psql(...)` for each unapplied migration; migration 003 runs `ALTER TABLE custom_data ADD COLUMN user_id` (003 lines 9-26), which needs an exclusive lock that the gate's own open transaction blocks. This matches the recorded memory note (reference_conport_migration_gate_deadlock). Workaround: apply `schema.sql` and migrations 001/002/003/004/007 directly with `psql` first, then run `gate apply` so it takes the adopt path (`scripts/migration/provision_conport_project_db.sh` does this). NOT_RUN live. A new column migration run through the gate would hit this on a fresh database but short-circuits on an already-migrated one.

Verdicts: conport_identity GO_REDUCED (changes 8, 10), conport_migration GO_REDUCED (operator step plus psql-then-adopt workaround).

## 9. Q8: orchestrator actor enforcement in this repo (design 5.5, W5)

- `.claude/hooks/orchestrator_enforcement.py`: `actor_authentication_enabled` (117-125) is true only when the config has `actor_authentication.enabled: true`; `actor_attribution_violation` (128-149) flags an `advance_item` or `manage_notes upsert` call whose elements lack a truthy `actor`; `actor_attribution_block` (152-163) returns the block reason only when both hold. Config discovery `find_orchestrator_config` (80-105).
- `src/dopemux/claude/native_hooks.py:438-444`: `needs_config = "advance_item" in tool_name or "manage_notes" in tool_name`; config text read; `actor_attribution_block(...)` result passed to `_deny_tool`. Lines 446-448 then run the DCP surface guard (`surface_guard_block`).
- `.taskorchestrator/config.yaml` has NO `actor_authentication` block (grep: no match in the file or anywhere else under `.taskorchestrator/`). The hook is dormant here, as `.claude/CLAUDE.md` says ("dormant until `actor_authentication.enabled`"). The design sentence "currently require an `actor` field" is true only for a repo that sets the flag. Because the block is absent, the "delete the block or startup fails" 4.0 break does not apply to this repo's config (it applies to other repos that enabled it; unknown which).
- Under 4.0 the hook matches names that no longer exist (`advance_item`, `manage_notes`), so it stops firing; it also would not flag a body `actor` (4.0 answers `unknown_parameter`).
- Tests asserting the actor requirement: `tests/test_orchestrator_enforcement_hooks.py` lines 28-30 (config strings), 60-80 (enabled detection), 85-125 (violation), 127-160 (block), 229 (`"actor_authentication" in found`), 240-258 (dispatcher blocks or allows `mcp__task-orchestrator__advance_item`); and `tests/unit/test_mcp_commands_catalog.py:516` asserts the generator output mentions `actor_authentication.enabled`. `tests/test_orchestrator_enforcement_hooks.py` is under `tests/` root, which CI does not run (ci-complete.yml runs `tests/unit`, `tests/dcp`, `tests/auditor_router`, `tests/integration`, a few named files): coverage there is local only. `fleet_catalog.py:306` and `:1195` and `mcp_commands.py:1100` also name `actor_authentication.enabled` as the precondition text (design change 12).
- The generator references: `docs/03-reference/mcp/feature-register.yaml:1978`.

## 10. Q9: generator gate (design 5.7, W6)

- `src/dopemux/commands/mcp_commands.py:916-917` declares `--allow-sequenced`; `:946` parameter; `:1032` passes it to `_apply_in_repo_agent_configs`; `:1079` is `if allow_sequenced:`; the refusal text at 1092-1104 names `DMX-MEMSPINE-IDENTITY-005` and `actor_authentication.enabled`. The flag checks neither prerequisite. Confirmed.
- Catalog rows with `agents.codex: full-sequenced`: seven, in both `mcp_catalog.yaml` (lines 207, 230, 274, 307, 562, 594, 630) and `src/dopemux/mcp/default_catalog.yaml` (same lines; the two files are byte-identical, `diff -q` silent): serena, dope-context, gpt-researcher, pal-stdio, conport, dope-memory, task-orchestrator. `fleet_catalog.py:78` `_CODEX_RENDERABLE_EXPOSURES = (None, "full", "full-sequenced")`; `:267` renders those; `:599-607` copilot.
- Rendering: Codex: `merge_codex_config_toml` (`fleet_catalog.py:390`) writes a marker-delimited `[mcp_servers.*]` region into the repo's `.codex/config.toml` only (written at `mcp_commands.py:1078-1090`); a preview always lands under the `--output-dir`. This repo's tracked `.codex/config.toml` has no `mcp_servers` today. The global `~/.codex/config.toml` is never written by the generator. OpenCode: `render_opencode_jsonc` (:541) managed region in `opencode.jsonc`; Copilot: `render_copilot_proxy_config` (:595) to `mcp-proxy-config.copilot.yaml`.
- Claude Code: not produced by `generate`. `.mcp.json` comes from `dopemux mcp init` through `_build_local_mcp_json` (`mcp_commands.py:887`) and `_render_local_entry` (:619), which emits `type`, `url` or `command`/`args`, and `${VAR:-}` env. `.mcp.json` is untracked in this repo (`git ls-files .mcp.json` empty). W6's "generator for Claude Code" therefore targets the `init`/`ensure` path, and `dopemux mcp ensure` compares `.mcp.json` against catalog defaults (`mcp_commands.py:1166`), so any Claude Code stdio entry change also changes what `ensure` considers drift.
- `catalog` and `default_catalog` must stay identical (W6 must edit both). `tests/test_mcp_config_generation.py` (tests/ root, not CI) and `tests/unit/test_mcp_commands_catalog.py` (CI) cover this.
- Verdict generator_gate: GO.

## 11. Q10: internal callers (design 5.3, W8)

Write paths in this repo, with file:line, server and route. Detail is in the GATE_TABLE `internal_callers` list; summary:

| Caller | Server and route | Observation |
|---|---|---|
| src/dopemux/pm/adapters/dope_memory.py:82, :110 | dope-memory POST /tools/memory_store, /tools/memory_correct (base `DOPE_MEMORY_URL`, default :3020, line 14) | The only dope-memory HTTP writer in the four named files. |
| src/dopemux/memory/capture_client.py:388, :455, :530 | dope-memory ledger file, no HTTP (`sqlite3.connect` at :530) | Direct SQLite writer; also runs the ledger migrations (:268). A bearer token cannot cover it. |
| src/dopemux/claude/native_hooks.py:128-175, :212 (import :83) | Redis XADD `dopemux:events` and `try_emit_promotable_capture_event` (capture_client) | No HTTP write route. Redis stream events are consumed into the ledger by `eventbus_consumer.py:404/431`. |
| services/working-memory-assistant/conport_client.py:14-26 | none | Imports `mcp__conport__*` modules that do not exist; falls back to mocks; no route. Also red-lane path. |
| src/dopemux/tools/conport_client.py:74, :103, :150 | ConPort REST POST /api/context/{ws}, /api/decisions, /api/progress | HTTP writer, not in W08's allowlist. |
| src/dopemux/instance_state.py:178, :217, :258, :400 | ConPort REST POST and DELETE /api/custom_data | Not in allowlist. |
| src/dopemux/profile_analytics.py:117, :226 | ConPort REST POST /api/custom_data | Not in allowlist. |
| src/dopemux/commands/decisions_commands.py:197, :236 | ConPort REST POST /api/decisions | Not in allowlist. |
| src/dopemux/adhd/rte_adapter.py:63 | ConPort REST POST /api/decisions | Not in allowlist. |
| src/dopemux/pm/adapters/conport.py:43, :147 | POST /kg/custom_data (not a route in `enhanced_server.py:245-281`; server UNKNOWN) | Not in allowlist. |
| services/adhd_engine/conport_client.py:67, :96, :143 | ConPort REST POST /api/context, /api/decisions, /api/progress | Not in allowlist. |
| services/claude_brain/brain_manager.py:293 | ConPort REST POST /api/decisions | Not in allowlist. |
| services/dopecon-bridge/dopecon_bridge/clients.py:231, :246, :249, :273 | ConPort REST POST /api/decisions, /api/progress, /api/custom_data, /api/custom_data/claim | Not in allowlist. |
| services/dopecon-bridge/ddg_mcp_stdio.py:97, :109, :117 | ConPort REST POST /api/instance/fork, /api/progress/promote, /api/progress/promote_all | Not in allowlist. |
| services/task-orchestrator (Python FastAPI, :8000) app/adapters/conport_adapter.py:588, :646, :739; task_orchestrator/adapters/auto_logger.py:55, :75, :107, :122 | ConPort REST POST /api/progress/log (no such route in the route table), PUT /api/progress/{id}, POST /api/progress and /api/decisions | Out of scope service (design non-goal) but an unauthenticated writer. |
| docker/mcp-servers-source/conport/server.py (lines in section 3), conport_mcp_stdio.py (:58, :85, :120, :131, :138, :154, :171, :198, :206) | ConPort REST, all 9 write routes | The SSE and stdio proxies themselves send no credentials; they are the "internal caller" that matters most for G2. |
| scripts/proof_conport_mcp.py:41 | ConPort REST POST /mcp tools/call `conport_log_progress` | Proof script. |
| dashboard/service_clients.py:320-390 (cockpit data client) | ConPort via `http://localhost:5455/conport/*` | GET only. The "cockpit client" in design 5.3 is UNKNOWN as a writer; this is the only candidate found and it reads. |
| JVM orchestrator :7890 | no in-repo programmatic HTTP caller found | Callers are runner MCP clients and `scripts/proofs/run_dnh_mcp_e2e.py`. `services/dopecon-bridge` talks to the separate Python orchestrator (`TASK_ORCHESTRATOR_URL`). |

Consequence for G2 and W8 (design changes 9 and 10): with bearer tokens only the HTTP writers can be covered, and there are at least fifteen of them outside W08's allowlist. The SQLite (capture_client, eventbus_consumer) and Redis (native_hooks) writers cannot present a token to a server; their identity would have to be either file-level (a writer-side principal column filled by the writer itself, which is self-asserted, not verified) or the paths must be routed through dope-memory's HTTP API. Without a decision, G2 as worded ("every call to the three servers carries a verified identity", "REST routes would stay an unauthenticated write path") is false even after W08.

## 12. Q11 and Q12: cross-repo reach, ports and catalog

Q11 (R05; `find ~/code -maxdepth 4`, pruning `node_modules` and `.worktrees`; `grep -l 7890`; paths only). The 27 `.mcp.json` paths are listed in the GATE_TABLE evidence. Counts:
- `.mcp.json` files found: 31; referencing 7890: 27. Without: `claude-mem-main/.mcp.json`, `claude-mem-main/plugin/.mcp.json`, `claude-mem/plugin/.mcp.json`, `image-processing/.mcp.json`.
- `.codex/config.toml` files found: 13; referencing 7890: 5 (`Dopemux-ChatRipperXXX`, `_worktrees/pr92-legacy-primary-independent-019`, `adOps`, `dopeClaw`, `dopemux-mvp` main checkout).
- Global configs checked (existence then `grep -q`): `~/.claude.json` HAS, `~/.codex/config.toml` HAS, `~/.commandcode/mcp.json` HAS; no 7890 in `~/.claude/settings.json`, `~/.claude/settings.local.json`, `~/.config/opencode/opencode.jsonc`, `~/.copilot/mcp-config.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`.
- Eleven of the 27 `.mcp.json` hits are dNh_CRM-family directories (the repo and its audit and fix worktrees), so distinct repos are fewer than 27.
- Does the design 5.6 dry run cover them? It names repo `.mcp.json` and `.codex/config.toml` under the code root plus the three global files: coverage of those files matches what was found. Gaps: (a) nested `.worktrees/` directories inside repos hold their own untracked `.mcp.json` copies (skipped here and not specified by the design); (b) depth beyond 4; (c) configs that reference the orchestrator through `${TASK_ORCHESTRATOR_HTTP_PORT}` or another port are invisible to a literal `7890` search; (d) Claude Desktop and other app configs were not scanned. The dry run should list its exclusions.

Q12 (registry, compose, catalog entries per workstream):
- W01: `compose.yml` dope-memory service (lines 585-625: host port `127.0.0.1:${DOPE_MEMORY_PORT:-3020}:3020`, env block 605-612, `./.dopemux:/data` volume); `services/registry.yaml` `dope-memory` port 3020; `mcp_catalog.yaml` and `default_catalog.yaml` `dope-memory` (http, `url_template` `http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp`); and `src/dopemux/mcp/docker_runtime.py:185-203` (per-worktree override) which is NOT in W01's allowlist. Auth-mode env and a read-only token-directory mount for per-worktree sidecars must be added there or via a new compose variable (design change 7).
- W02: `compose.yml` conport service (line 233 onward; container ports 3004, 3005; `docker_runtime.py:161-183` publishes 3004, 3005, 4004); `registry.yaml` `conport-http` 3004 and `conport-mcp` 3005; catalog `conport` (transport `sse`, `url_template` `.../sse`, `port_var CONPORT_MCP_PORT`, `extra_port_vars`). A streamable surface on the existing 3005 listener avoids a new registry or catalog port; a new port needs entries in all four places.
- W05/W06: catalog `task-orchestrator` (http, `http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp`, `reserved_port 7890`); registry `task-orchestrator` port 8000 is the Python service (a known accepted exception in the drift test).
- Port-drift test (PR #1485, unmerged; commit `9bbb4f853` on `feat/foundations-wave-1`, read locally with `git show`): `tests/arch/test_service_port_drift.py` checks catalog ports against `services/registry.yaml`, compose host ports against the registry, hard-coded `localhost:<port>` literals in a fixed file list (manager.py, dopemux_dashboard.py, statusline.sh, mcp_server_health_report.sh, mcp_health_check.sh, service_endpoints.py, profile_detector.py), and Dope layout defaults. It would constrain W01, W02 and W06 only if they change a port, a registry port, a compose host mapping or a catalog `url_template` port; an unchanged-port auth change does not touch it. It has a documented exception for `task-orchestrator`.

## 13. Red lane finding (authority conflict; blocks W01, W02 and part of W08)

- `src/dopemux/dcp/red_lane_rules.py:84-86` `FORBIDDEN_PATHS` includes `^services/working-memory-assistant/.*\Z`, `^docker/mcp-servers-source/conport/.*\Z`, `^src/conport/.*\Z`.
- `.claude/hooks/dcp_surface_guard.py` (RED_LANE_ID `DCP-RED-MERGE-SEAM-0001`) hard-denies Edit/Write on those paths, and `src/dopemux/claude/native_hooks.py:446-448` turns the guard result into `_deny_tool`. `tests/test_dcp_surface_guard.py:211-221` asserts `services/working-memory-assistant/src/mcp/server.py` stays blocked.
- `tools/pr_steward/security_release_gate.py:56-82` classifies a PR touching those paths as `dcp_boundary`, meaning explicit security or release approval before READY.
- Precedent for relief: ADR-224 (workflow files) and ADR-226 (dope-context eval) are narrow, ADR-anchored carve-outs with matching test changes. None exists for dope-memory or ConPort.
- W01's allowlist (`services/working-memory-assistant/...`), W02's (`docker/mcp-servers-source/conport/`) and W08's `services/working-memory-assistant/conport_client.py` all fall inside. Per C07 this is a stop, not something to route around. Clearing action: operator-approved narrow carve-out ADR plus the `red_lane_rules.py`, `dcp_surface_guard.py` fallback list and test updates (all outside W01/W02 allowlists), or an operator decision to run W01 and W02 on a non-Claude runner with the `dcp_boundary` approval recorded.

## 14. W05 scope and a possible split (for the supervisor)

The orchestrator 4.0.0 change is larger than "pin, config, token auth, two hooks":
1. Pin: no published 4.0.0 (section 2). Everything below can be built and unit-tested without a digest only if the digest is a required operator-supplied input that the cutover refuses to default.
2. Wrapper env: add `API_ENABLED=true`, `API_AUTH_MODE=bearer`, `API_TOKENS_PATH`, a read-only token directory mount (mount a directory, not the single file, so an atomic replace on rotation is seen; unverified Docker behaviour, flagged), drop `USE_FLYWAY`, set `RETENTION_*`, raise the health `--start-period`.
3. Config: rewrite `.taskorchestrator/config.yaml` to the 4.0 grammar; validate with the upstream `config validate` op once a 4.0 server exists (NOT_RUN today).
4. Tool surface: every 3.x tool reference (section 2) must move to the 4.0 tools or be disabled; `/dx:*` commands, hooks, manifest, profile policy.
5. Hooks: `orchestrator_enforcement.py` and `native_hooks.py:438-444` stop matching dead names.
6. Cutover command with dry run, volume copy, `.bak` check, rollback.
Minimum honest split: W05a (wrapper env, token-file writer, cutover command, rollback, hooks neutering) and W05b (config and 3.x-to-4.0 tool-surface migration), with W05b possibly its own macropacket.

## 15. Probe table

| ID | Command (loopback, `curl -sS -m 3` unless noted) | curl exit | HTTP | Bucket | Result |
|---|---|---|---|---|---|
| L1 | `python3 -I proof/.../conport_parity_probe.py 3019 3007` | script exit 0 | REST 200, SSE ok | PASS | R06 reproduced live (13 REST, 17 SSE, initialize -32601) |
| P1 | GET http://127.0.0.1:3054/health | 0 | 200 | PASS | `{"status":"healthy","service":"dope-memory","version":"1.0.0"}` |
| P2 | POST :3054/mcp `initialize`, Accept json+sse | 0 | 200 | PASS | SSE-framed; `mcp-session-id` issued; serverInfo dope-memory 3.4.7 |
| P3 | POST :3054/mcp `notifications/initialized` + session id | 0 | 202 | PASS | empty body |
| P4 | POST :3054/mcp `tools/list` + session id | 0 | 200 | PASS | 10 memory_* tools |
| P5 | POST :3054/mcp `initialize`, Accept json only | 0 | 406 | PASS | rejection confirms Accept rule |
| P6 | POST :3054/mcp `tools/list`, no session | 0 | 400 | PASS | "Missing session ID" |
| P7 | GET http://127.0.0.1:7890/health | 0 | 404 | PASS | 3.8.0 has no /health |
| P8 | POST :7890/mcp `initialize`, Accept json+sse | 0 | 200 | PASS | JSON body; session id; 3.8.0; 14 3.x tools named in instructions |
| P9 | POST :7890/mcp `notifications/initialized` + session id | 0 | 202 | PASS | |
| P10 | POST :7890/mcp `tools/list` + session id | 0 | 200 | PASS | 14 tools: manage_items ... get_context |
| P11 | POST :7890/mcp `tools/list`, Accept json only, no session | 0 | 406 | PASS | |
| N1 | any 4.0 server probe | n/a | n/a | NOT_RUN | no 4.0 server exists locally; no pull allowed |
| N2 | `GET /health` or tools/list on ConPort :3019/:3007 beyond L1 | n/a | n/a | NOT_RUN | L1 covers it |

No `tools/call` or write route was sent. Sessions P2 and P8 were opened and left to expire server-side (no DELETE sent). No container was started, stopped or inspected.

## 16. Design changes, authority conflicts, reductions (summary)

Design changes (full list with sections and affected workstreams in the GATE_TABLE `design_changes`): 1 pin unavailable; 2 config grammar break; 3 tool-surface break; 4 wrapper env break; 5 token file shape and principal naming; 6 dope-memory SQLite migration is automatic and `migration_runner.py` is the wrong file; 7 sidecar env lives in `docker_runtime.py`; 8 ConPort write-route list and REST data-plane auth; 9 internal callers: direct SQLite and Redis writers; 10 W08 caller set; 11 fresh worktree has no `.envrc.dopemux-mcp`; 12 gate text references a removed 3.x setting; 13 CI does run one dope-memory test; 14 ConPort transport choice.

Authority conflicts (design versus runtime or packet versus runtime): see GATE_TABLE `authority_conflicts`. Per C08 none was silently resolved: the runtime fact is reported and the design is untouched.

Unknowns: see GATE_TABLE `unknowns`.

## 17. GATE_TABLE

Verdict key for the nested `V` fields: `body_actor_refused`, `permissive_phase`, `migration_reversible` = verdict on what the design assumes about 4.0 (GO = assumption holds, NO_GO = it does not); `dope_memory_identity`, `conport_identity`, `conport_migration`, `generator_gate` = whether the design's change is technically buildable as designed; `workstream_go` = whether the workstream may start as packeted.

```json
{
  "orchestrator_v4": {
    "upstream_repo": "jpicklyk/task-orchestrator",
    "image_ref_current": "ghcr.io/jpicklyk/task-orchestrator@sha256:e47ed00aae313a85de0e6340010bfec8bdcd5f8c253d002759a4bb1ef8c122c1 (commented v3.8.0; scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:4)",
    "image_ref_4_0_0": "UNKNOWN. Documented as ghcr.io/jpicklyk/task-orchestrator:4.0.0 (server.json, fleet-deployment.md:1010) but upstream has no v4.0.0 tag or release (latest v3.16.0) and docker-publish.yml publishes only on v* tag pushes; no digest obtainable without a pull",
    "auth_setting": "API_ENABLED=true plus API_AUTH_MODE=bearer|jwks (or none with API_ALLOW_UNAUTHENTICATED=true); MCP_TRANSPORT=http without the API fails startup (MCP_AUTH) unless MCP_ALLOW_UNAUTHENTICATED=true. Design name API_AUTH_MODE confirmed; API_ENABLED requirement is new. JWKS: API_AUTH_MODE=jwks with API_JWKS_URL (https; public hosts only), API_JWKS_ISSUER, API_JWKS_AUDIENCE, API_JWKS_ALGORITHMS",
    "token_file_format": "YAML at API_TOKENS_PATH (default /run/secrets/api-tokens.yaml): version: 1; tokens[] with id (audited as api:<id>), token_sha256 (64 lowercase hex of exact token bytes, no trailing newline), capabilities[] (required to grant anything), optional kind human|agent|service (default service), profile director, scope.root_ids/tags_include, expires_at, description; unknown entry keys fail startup; loaded once, rotation needs restart",
    "body_actor_refused": "GO",
    "permissive_phase": "NO_GO",
    "sqlite_path": "/app/data/current-tasks.db (DATABASE_PATH set by both wrappers; image default data/current-tasks.db relative to /app; VOLUME /app/data)",
    "migration_reversible": "GO_REDUCED"
  },
  "conport_transport": {
    "choice": "STREAMABLE_HTTP_APP",
    "verdict": "GO",
    "sse_only_write_tools": [
      "fork_instance",
      "promote",
      "promote_all"
    ]
  },
  "bridge": {
    "handshake": "POST <base>/mcp with Accept: application/json, text/event-stream (406 otherwise); initialize first; capture mcp-session-id from the initialize response header and echo it on every later request (400 Missing session ID otherwise); responses are SSE-framed on dope-memory (event: message / data: {json}) and plain JSON on the 3.8.0 orchestrator, so parse both; notifications/initialized returns 202 with an empty body and must produce no stdout line; 4.0 orchestrator adds Authorization: Bearer on every request (401 unauthenticated envelope, session bound to principal). ConPort has no streamable surface today (REST /mcp answers initialize with -32601; SSE is a different transport), so its leg waits for W02",
    "verdict": "GO_REDUCED"
  },
  "keychain_noninteractive": "NOT_RUN",
  "dope_memory_identity": "GO_REDUCED",
  "conport_identity": "GO_REDUCED",
  "conport_migration": "GO_REDUCED",
  "generator_gate": "GO",
  "internal_callers": [
    {
      "caller": "src/dopemux/pm/adapters/dope_memory.py",
      "server": "dope-memory",
      "route": "POST /tools/memory_store; POST /tools/memory_correct (base DOPE_MEMORY_URL, default http://localhost:3020)",
      "evidence": "dope_memory.py:14, :82, :110"
    },
    {
      "caller": "src/dopemux/memory/capture_client.py",
      "server": "dope-memory ledger file (no HTTP)",
      "route": "direct sqlite3 write to .dopemux/chronicle.sqlite; also applies ledger migrations",
      "evidence": "capture_client.py:388, :455, :530 (sqlite3.connect), :268"
    },
    {
      "caller": "src/dopemux/claude/native_hooks.py",
      "server": "redis-events and dope-memory ledger (no HTTP)",
      "route": "XADD dopemux:events; try_emit_promotable_capture_event into capture_client",
      "evidence": "native_hooks.py:83, :128-175, :212"
    },
    {
      "caller": "services/working-memory-assistant/eventbus_consumer.py",
      "server": "dope-memory ledger (no HTTP)",
      "route": "Redis stream consumer writing insert_raw_event, insert_promoted_entry, insert_reflection_card",
      "evidence": "eventbus_consumer.py:404, :431, :672"
    },
    {
      "caller": "services/working-memory-assistant/conport_client.py",
      "server": "conport (none in practice)",
      "route": "imports mcp__conport__* modules that do not exist; mock fallback; no route",
      "evidence": "conport_client.py:14-26"
    },
    {
      "caller": "src/dopemux/tools/conport_client.py",
      "server": "conport REST",
      "route": "POST /api/context/{ws}; POST /api/decisions; POST /api/progress",
      "evidence": "conport_client.py:74, :103, :150"
    },
    {
      "caller": "src/dopemux/instance_state.py",
      "server": "conport REST",
      "route": "POST /api/custom_data; DELETE /api/custom_data",
      "evidence": "instance_state.py:178, :217, :258, :400"
    },
    {
      "caller": "src/dopemux/profile_analytics.py",
      "server": "conport REST",
      "route": "POST /api/custom_data",
      "evidence": "profile_analytics.py:117, :226"
    },
    {
      "caller": "src/dopemux/commands/decisions_commands.py",
      "server": "conport REST",
      "route": "POST /api/decisions",
      "evidence": "decisions_commands.py:197, :236"
    },
    {
      "caller": "src/dopemux/adhd/rte_adapter.py",
      "server": "conport REST",
      "route": "POST /api/decisions",
      "evidence": "rte_adapter.py:62-63"
    },
    {
      "caller": "src/dopemux/pm/adapters/conport.py",
      "server": "UNKNOWN (route /kg/custom_data is not in the ConPort route table enhanced_server.py:245-281)",
      "route": "POST /kg/custom_data",
      "evidence": "conport.py:43, :147"
    },
    {
      "caller": "services/adhd_engine/conport_client.py",
      "server": "conport REST",
      "route": "POST /api/context/{ws}; POST /api/decisions; POST /api/progress",
      "evidence": "conport_client.py:67, :96, :143"
    },
    {
      "caller": "services/claude_brain/brain_manager.py",
      "server": "conport REST",
      "route": "POST /api/decisions",
      "evidence": "brain_manager.py:293"
    },
    {
      "caller": "services/dopecon-bridge/dopecon_bridge/clients.py",
      "server": "conport REST",
      "route": "POST /api/decisions; POST /api/progress; POST /api/custom_data; POST /api/custom_data/claim",
      "evidence": "clients.py:231, :246, :249, :273"
    },
    {
      "caller": "services/dopecon-bridge/ddg_mcp_stdio.py",
      "server": "conport REST",
      "route": "POST /api/instance/fork; POST /api/progress/promote; POST /api/progress/promote_all",
      "evidence": "ddg_mcp_stdio.py:97, :109, :117"
    },
    {
      "caller": "services/task-orchestrator (Python FastAPI :8000, out of scope service)",
      "server": "conport REST",
      "route": "POST /api/progress/log (not in the route table); PUT /api/progress/{id}; POST /api/progress; POST /api/decisions",
      "evidence": "app/adapters/conport_adapter.py:588, :646, :739; task_orchestrator/adapters/auto_logger.py:55, :75, :107, :122"
    },
    {
      "caller": "docker/mcp-servers-source/conport/server.py (SSE proxy :3005)",
      "server": "conport REST :3004",
      "route": "all 9 write tools: PUT /api/progress/{id}; POST /api/decisions; POST /api/instance/fork; POST /api/progress/promote; POST /api/progress/promote_all; POST /api/context/{ws}; POST /api/progress; POST /api/custom_data; DELETE /api/custom_data",
      "evidence": "server.py:55-205 (no auth header, no instance id)"
    },
    {
      "caller": "docker/mcp-servers-source/conport/conport_mcp_stdio.py (stdio proxy)",
      "server": "conport REST",
      "route": "same 9 write routes",
      "evidence": "conport_mcp_stdio.py:58, :85, :120, :131, :138, :154, :171, :198, :206"
    },
    {
      "caller": "scripts/proof_conport_mcp.py",
      "server": "conport REST",
      "route": "POST /mcp tools/call conport_log_progress",
      "evidence": "proof_conport_mcp.py:41"
    },
    {
      "caller": "dashboard/service_clients.py (cockpit data client candidate)",
      "server": "conport via gateway :5455",
      "route": "GET only (get_decisions, get_active_context, get_progress)",
      "evidence": "service_clients.py:320-390; no write route; the design's cockpit writer is UNKNOWN"
    },
    {
      "caller": "JVM task orchestrator :7890",
      "server": "task-orchestrator",
      "route": "no in-repo programmatic HTTP caller found; callers are runner MCP clients and scripts/proofs/run_dnh_mcp_e2e.py; services/dopecon-bridge targets the separate Python orchestrator",
      "evidence": "rg over src, scripts, services; dopecon_bridge/config.py:82-83"
    }
  ],
  "cutover_scope": {
    "repo_mcp_json": 27,
    "repo_codex_toml": 5,
    "global_configs": [
      "/Users/hue/.claude.json",
      "/Users/hue/.codex/config.toml",
      "/Users/hue/.commandcode/mcp.json"
    ]
  },
  "workstream_go": {
    "W01": "NO_GO",
    "W02": "NO_GO",
    "W03": "GO",
    "W04": "GO_REDUCED",
    "W05": "NO_GO",
    "W06": "GO_REDUCED",
    "W07": "GO_REDUCED",
    "W08": "GO_REDUCED"
  },
  "design_changes": [
    {
      "section": "5.5, 5.10, W5",
      "change": "Upstream has no v4.0.0 tag or release (latest v3.16.0); the image is presumably unpublished. The pin cannot be set to a verified digest. W05 must take the 4.0.0 digest as an operator-supplied, refused-if-absent input, or wait for upstream.",
      "affects": [
        "W05",
        "W06",
        "W07"
      ]
    },
    {
      "section": "5.5, W5",
      "change": "Repo .taskorchestrator/config.yaml (628 lines) fails the 4.0 strict boot import: top-level schemas_metadata, uppercase lifecycle values including AUTO_REOPEN, and a top-level traits registry written as bare lists. Config must be rewritten to the 4.0 grammar and validated with the upstream config validate op once a 4.0 server exists. The actor_authentication block named in the packet and design is NOT present in this file.",
      "affects": [
        "W05"
      ]
    },
    {
      "section": "5.5, 5.10, W5",
      "change": "4.0 removes the whole 3.x tool layer (manage_items, query_items, advance_item, claim_item, manage_notes, query_notes, manage_dependencies, get_context, get_next_item, get_blocked_items, create_work_tree). 24 files under .claude/ (15 of 18 /dx:* commands, 3 orchestrator hooks, output style), .taskorchestrator/surface_manifest.json, templates/plugin/l0_membership.json, mcp_tool_surfaces.json, src/dopemux/mcp/profile_policy.py, src/dopemux/pcp/task_orchestrator_projection.py and several tests call them. W05's write_surface covers none of these except two hooks. Split W05 (wrapper/token/cutover/hooks) from a tool-surface migration packet.",
      "affects": [
        "W05",
        "W06",
        "W07"
      ]
    },
    {
      "section": "5.5, 5.6, W5",
      "change": "Orchestrator 4.0 has no log-only phase and a wrapper that still sets MCP_TRANSPORT=http without API_ENABLED fails startup (MCP_AUTH). Wrapper must add API_ENABLED=true, API_AUTH_MODE=bearer, API_TOKENS_PATH and a read-only token directory mount, drop USE_FLYWAY, decide RETENTION_*, raise the health start-period. The cutover is atomic per server; the 5.5 'log then enforce' rollout applies only to dope-memory and ConPort.",
      "affects": [
        "W05",
        "W03"
      ]
    },
    {
      "section": "5.2",
      "change": "Orchestrator token entries need id, token_sha256, a capabilities list and a kind; the audit principal becomes api:<id>. The shared hash file helper must emit the orchestrator YAML shape (and a different shape for the memory servers), define the id-to-principal mapping (runner:codex vs api:runner:codex), and treat rotation as a restart-requiring operator step for the orchestrator.",
      "affects": [
        "W03",
        "W05",
        "W08"
      ]
    },
    {
      "section": "5.9, W1",
      "change": "dope-memory's SQLite ledger migrates automatically on first use (chronicle/store.py:103-116, sqlite_migrations.py:74) by the server and by capture_client.py:268 from any hook process, with no dry run; services/working-memory-assistant/migration_runner.py is the WMA Postgres runner, not the ledger migrator. W1 should target chronicle/migrations/*.sql and chronicle/schema.sql and accept that a nullable-column migration is applied by whichever process touches the ledger first.",
      "affects": [
        "W01",
        "W08"
      ]
    },
    {
      "section": "5.1, W1, W2",
      "change": "Per-worktree sidecar identity and env come from src/dopemux/mcp/docker_runtime.py:161-203 (generated compose override), not compose.yml. Auth-mode env and the read-only token-directory mount for sidecars must be added there; that file is in no packet's write_surface. generate_mcp_env also drops keys containing TOKEN or PASSWORD.",
      "affects": [
        "W01",
        "W02",
        "W05"
      ]
    },
    {
      "section": "5.1, W2",
      "change": "ConPort write surface is larger than the design lists: also DELETE /api/custom_data, POST /api/custom_data/claim, POST /api/instance/fork, POST /api/progress/promote, POST /api/progress/promote_all, and POST /mcp tools/call for 9 write tools (3 callable but unlisted). Only workspace_contexts and progress_entries carry instance_id; decisions has created_by_instance and custom_data has no instance column, so 'shared lands where NULL lands' has no meaning for those two. The SSE proxy (server.py) forwards to REST with no credentials, so auth on :3005 without auth on :3004 leaves the data plane open; :3004 is published on host loopback.",
      "affects": [
        "W02"
      ]
    },
    {
      "section": "5.3, G2, W8",
      "change": "capture_client.py, native_hooks.py (Redis XADD) and eventbus_consumer.py write the SQLite ledger or the Redis stream without any server credential, and services/working-memory-assistant/conport_client.py is a mock. G2 ('every call to the three servers carries a verified identity') cannot hold for these writers through bearer tokens. Either re-word G2 to cover HTTP callers only and record the file-level writers as self-asserted internal principals, or route them through dope-memory's HTTP API.",
      "affects": [
        "W01",
        "W08",
        "W07"
      ]
    },
    {
      "section": "5.3, W8",
      "change": "W08's allowlist names 4 files; at least 15 more in-repo callers send unauthenticated ConPort REST writes (see internal_callers). Either widen W08 (or add a ConPort-client packet) or accept that REST write routes stay open and G2 is partial. The 'cockpit client' writer is UNKNOWN; dashboard/service_clients.py reads only.",
      "affects": [
        "W08",
        "W02"
      ]
    },
    {
      "section": "5.1, 5.3",
      "change": "A fresh worktree has no .envrc.dopemux-mcp unless dopemux mcp init runs there (it is gitignored, per checkout). The bridge's walk-up discovery finds nothing in such a worktree and must fail closed with an instruction to run dopemux mcp init; falling back to the main checkout's file would bind a worktree to the wrong containers. Read only *_PORT keys via safe_port_int; the file also exports a database password.",
      "affects": [
        "W04",
        "W06"
      ]
    },
    {
      "section": "5.7, W6",
      "change": "Gate text and tests name actor_authentication.enabled (a removed 3.x setting): mcp_commands.py:1100, fleet_catalog.py:306 and :1195, tests/unit/test_mcp_commands_catalog.py:516. Replace with the 4.0 check (token auth on, from the 4.0 /api/v1/info verifier field once available). Claude Code config is produced by mcp init (_build_local_mcp_json, _render_local_entry), not generate; mcp ensure compares .mcp.json to catalog defaults, so changes there change drift detection. mcp_catalog.yaml and default_catalog.yaml are byte-identical and must change together.",
      "affects": [
        "W06"
      ]
    },
    {
      "section": "8, W1",
      "change": "CI does run one dope-memory test: ci-complete.yml:195-199 runs services/working-memory-assistant/tests/test_mcp_http_endpoint.py, which calls build_mcp_server(get_server, default_workspace_id, default_instance_id). Removing the defaults changes that signature and must update this test. tests/test_orchestrator_enforcement_hooks.py and tests/test_mcp_config_generation.py sit at tests/ root, which CI does not run.",
      "affects": [
        "W01",
        "W05",
        "W06"
      ]
    },
    {
      "section": "5.4, W2",
      "change": "ConPort transport: choose a streamable-HTTP app (mcp 1.29.0 FastMCP.streamable_http_app) mounted on the existing :3005 listener beside sse_app(); exposes the same 17 unprefixed tool names Claude Code sees today. REST_JSONRPC would need initialize and notifications/initialized added to the unauthenticated data-plane handler, prefixed names and 13 listed tools. The design's statement that the :3004 surface is what the bridge expects holds only for tools/list and tools/call.",
      "affects": [
        "W02",
        "W04",
        "W06"
      ]
    },
    {
      "section": "5.6",
      "change": "Cutover dry run should state its exclusions: nested .worktrees/ copies of .mcp.json, depth beyond the scan, configs that reach the orchestrator through ${TASK_ORCHESTRATOR_HTTP_PORT} or another port (a literal 7890 search misses them), and app configs such as Claude Desktop. Measured: 27 of 31 .mcp.json and 5 of 13 .codex/config.toml under ~/code reference 7890, plus 3 global configs.",
      "affects": [
        "W05"
      ]
    },
    {
      "section": "0, 7, W1, W2, W8",
      "change": "Red lane DCP-RED-MERGE-SEAM-0001 (red_lane_rules.py:84-86) hard-denies edits under services/working-memory-assistant/** and docker/mcp-servers-source/conport/** from Claude Code sessions and marks PRs touching them dcp_boundary for PR Steward. W01, W02 and W08's conport_client.py cannot start without an operator-approved narrow carve-out (ADR-224/226 pattern) or a recorded decision to run them on a non-Claude runner with the approval.",
      "affects": [
        "W01",
        "W02",
        "W08"
      ]
    }
  ],
  "reductions": [
    "W05 reduced scope (if the supervisor accepts a split): W05a wrapper env, token-file writer and mount, cutover command with dry run, volume copy and .bak verification, rollback, and hook neutering, with the 4.0.0 digest as a required operator-supplied input that the command refuses to default; the config rewrite and tool-surface migration move to a separate packet validated against a real 4.0 server.",
    "W04 reduced scope: bridge supports per-server profiles; dope-memory and orchestrator profiles are verifiable now (probe-recorded handshakes); the ConPort profile is verified only after W02 lands the streamable surface.",
    "W06 reduced scope: Codex via generate (--apply) with the real gate; Claude Code via mcp init/ensure; gate check 2 (orchestrator token auth) stays unsatisfiable, so no write-capable Codex orchestrator entry is applied, until W05 is activated by the operator.",
    "W07 reduced scope: how-to and ADR amendment drafts can be written now; the live Codex acceptance run is operator-run and NOT_RUN.",
    "W08 reduced scope: pm/adapters/dope_memory.py (the only dope-memory HTTP writer among the four named files); capture_client.py and native_hooks.py need the G2 wording decision; services/working-memory-assistant/conport_client.py excluded (mock, red lane).",
    "G2 reduced wording (proposal): verified principal on every HTTP write to the three servers; file-level and Redis writers recorded as self-asserted internal principals until routed through HTTP."
  ],
  "authority_conflicts": [
    "Packet Q1 / design 5.5 expect upgrade to orchestrator 4.0.0; upstream has no v4.0.0 tag or release (latest v3.16.0). Runtime fact reported; design not changed.",
    "Design 5.4: 'REST child already answers plain JSON-RPC POST /mcp on :3004, which is what the stdio bridge expects'. Runtime: REST answers initialize with -32601 (probe L1, enhanced_server.py:1816-1840); the bridge forwards initialize unchanged (http_stdio_bridge.py:143-158).",
    "Design section 1 and packet Q8: hooks 'require an actor field' and 'the actor_authentication block in .taskorchestrator/config.yaml'. Runtime: the block does not exist in this repo's config; the hook is dormant (orchestrator_enforcement.py:117-125).",
    "Packet C11 'services/*/tests and docker/*/tests are not run by CI'. Runtime: ci-complete.yml:195-199 runs services/working-memory-assistant/tests/test_mcp_http_endpoint.py.",
    "Packet Q6 and W01 allowlist: migration_runner.py as the dope-memory migration mechanism. Runtime: it is the WMA Postgres runner; the ledger migrates through chronicle/sqlite_migrations.py automatically.",
    "Design 5.3 and W08: internal callers 'read their token and send it' for native_hooks.py, capture_client.py, conport_client.py. Runtime: native_hooks writes Redis and capture_client writes SQLite directly; conport_client.py is a mock; none has an HTTP route to authenticate.",
    "Design G1/W1/W2 write allowlists versus DCP red lane FORBIDDEN_PATHS (red_lane_rules.py:84-86) and tests/test_dcp_surface_guard.py:211-221. Runtime wins; W01 and W02 stop.",
    "Design 5.1 'workspace_id/instance_id required on every mutating tool' versus ConPort storage: decisions and custom_data have no instance column (schema.sql:33-47, :109-118)."
  ],
  "unknowns": [
    "Whether ghcr.io/jpicklyk/task-orchestrator:4.0.0 exists and its digest (registry not queried; no pull allowed).",
    "Live 4.0 behaviour: body actor refusal, 401 envelope, session binding, config boot import result for this repo's config, and migration of this machine's 3.8.0 databases (schema version 17 or lower is assumed, not observed).",
    "Keychain non-interactive read and ACL prompt behaviour (procedure written, NOT_RUN).",
    "Whether conport_migration_gate.py REQUIRED_MIGRATIONS must be extended for a new migration file to verify.",
    "Which caller invokes upsert_trajectory_state (chronicle/store.py:1070) and whether memory_recap or memory_trajectory write.",
    "Exact mcp version in the running ConPort image (SSE serverInfo reports 1.30.0; repo lock has 1.29.0; Dockerfile resolves unlocked).",
    "Server behind src/dopemux/pm/adapters/conport.py POST /kg/custom_data; the design's 'cockpit client' writer.",
    "Whether Docker Desktop bind-mounting a single token file survives an atomic replace on rotation (mount a directory instead; unverified).",
    "Whether other machines or Claude Desktop and other app configs reference the orchestrator (not scanned)."
  ],
  "evidence": {
    "orchestrator_v4": [
      "gh release view v4.0.0 -R jpicklyk/task-orchestrator -> 'release not found'; gh release list: v3.16.0 Latest 2026-10-02",
      "gh api repos/jpicklyk/task-orchestrator/git/matching-refs/tags/v4 -> no refs; highest tag v3.16.0",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/version.properties (main d9efd9f1546aa3020b54467366a215d378e8bbb3 and release/4.0 75df163d7747d0fca9e4d050d2087d1c161366a2): VERSION_MAJOR=4 VERSION_MINOR=0 VERSION_PATCH=0",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/server.json: \"identifier\": \"ghcr.io/jpicklyk/task-orchestrator:4.0.0\"",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/.github/workflows/docker-publish.yml lines 3-6: on: push: tags: - 'v*'",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/CHANGELOG.md:60: 'Clients stop sending `actor`: the caller is the transport principal, and a body `actor` is `unknown_parameter`.'",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/CHANGELOG.md:46: 'The backup is the supported rollback, and a 3.x binary cannot open a V26 or later database.'",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/CHANGELOG.md:63-64: DEGRADED_MODE_POLICY and actor_authentication removed; a leftover value or block fails startup",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/fleet-deployment.md:24: '`API_ENABLED=true` with `API_AUTH_MODE=bearer` or `jwks` | Credential'",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/fleet-deployment.md:473-475, :498, :508 (API_AUTH_MODE, API_TOKENS_PATH, token_sha256, restart on rotation)",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/api-rest.md:70-116 (token file format version 1)",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/current/docs/config-reference.md:192-194, :255-262 (strict lowercase enums; boot import is strict)",
      "https://github.com/jpicklyk/task-orchestrator/blob/main/Dockerfile:53,56,60,89 (VOLUME /app/data, MCP_TRANSPORT=stdio, MCP_HTTP_PORT=3001, DATABASE_PATH=data/current-tasks.db)",
      "scripts/mcp-wrappers/task-orchestrator-current-stdio.sh:4,213-215; task-orchestrator-http-singleton.sh:34-36,182-191",
      "probe P8/P10: running orchestrator serverInfo mcp-task-orchestrator-current 3.8.0 with 14 3.x tools"
    ],
    "conport_transport": [
      "docker/mcp-servers-source/conport/server.py:43-229 (17 tools, sse_app only when argv sse)",
      "docker/mcp-servers-source/conport/enhanced_server.py:276 (POST /mcp), :1816-1840 (mcp_endpoint), :1981-2151 (13 listed tools), dispatch_map 16 names",
      "probe L1: rest_initialize -32601; rest_tools_list 13; sse 17 (server conport 1.30.0); identical false",
      ".venv mcp 1.29.0 server/fastmcp/server.py:821 sse_app, :953 streamable_http_app; pyproject.toml:112,:352 mcp>=1.28.1,<2; uv.lock mcp 1.29.0",
      "R06 hashes verified: PRE_ISSUANCE_CONPORT_PARITY.json cf7bbeed...c91; conport_parity_probe.py 8f70cdc7...b05"
    ],
    "bridge": [
      "src/dopemux/mcp/http_stdio_bridge.py:64,70-73 (POST /mcp, Accept application/json only), :95-96 (empty body error), :124-158 (loop), :23,47-60 (timeout)",
      "probes P2-P6, P8-P11 (handshake behaviour)",
      "src/dopemux/mcp/envrc.py:79 is_secret_like_key, :133 parse_envrc_text, :217 safe_port_int",
      "src/dopemux/config/manager.py:721 (only in-repo user of the bridge)",
      ".gitignore:411 (.envrc.dopemux-mcp ignored); worktree has no .envrc.dopemux-mcp"
    ],
    "keychain": [
      "security help add-generic-password: 'By default, the application which creates an item is trusted to access its data without warning.'; -T, -A, -U, '-w as the last option to be prompted'",
      "security help find-generic-password: '-w  Display only the password on stdout'",
      "security usage line: 'security [-h] [-i] ...' (-i interactive mode)",
      "Result NOT_RUN: no keychain item created, read or deleted"
    ],
    "dope_memory_identity": [
      "services/working-memory-assistant/dope_memory_main.py:57-58,111-139,287,431,452,560,608,795-816,1150-1346",
      "services/working-memory-assistant/mcp_http.py:69-316 (10 tools; defaults at 115-116)",
      "services/working-memory-assistant/canonical_ledger.py (resolve_canonical_ledger order)",
      "services/working-memory-assistant/chronicle/store.py:103-116, sqlite_migrations.py:74",
      "src/dopemux/memory/capture_client.py:262,268,530",
      "compose.yml:607-609; src/dopemux/mcp/docker_runtime.py:185-203",
      ".github/workflows/ci-complete.yml:195-199"
    ],
    "conport_identity": [
      "docker/mcp-servers-source/conport/instance_detector.py:52-78",
      "docker/mcp-servers-source/conport/enhanced_server.py:245-281 (route table), handlers 507-1332",
      "docker/mcp-servers-source/conport/schema.sql:12-21,33-47,61-72,109-118; migrations/007_worktree_support_simple.sql:12-24"
    ],
    "conport_migration": [
      "docker/mcp-servers-source/conport/enhanced_server.py:409-495 (_ensure_schema; operator-gated note)",
      "docker/mcp-servers-source/conport/migrations/conport_migration_gate.py:592-631 (apply_migrations), :646-690 (CLI)",
      "migrations/003_multi_tenancy_foundation.sql:9-26 (ALTER TABLE custom_data)",
      "memory note reference_conport_migration_gate_deadlock (workaround psql-then-adopt via scripts/migration/provision_conport_project_db.sh); NOT_RUN live"
    ],
    "generator_gate": [
      "src/dopemux/commands/mcp_commands.py:916-917,946,1032,1079,1092-1104",
      "mcp_catalog.yaml lines 207,230,274,307,562,594,630 (identical in src/dopemux/mcp/default_catalog.yaml; diff -q silent)",
      "src/dopemux/mcp/fleet_catalog.py:78,267,390,541,595",
      "src/dopemux/commands/mcp_commands.py:619-651,887-899"
    ],
    "internal_callers": [
      "rg over src, scripts, services, docker for /tools/memory_*, /api/decisions|progress|custom_data|instance/fork, DOPE_MEMORY_URL (excluding tests, docs, proof)",
      "src/dopemux/claude/native_hooks.py:83,128-175,212; src/dopemux/memory/capture_client.py:388,455,530"
    ],
    "cutover_scope": [
      "find ~/code -maxdepth 4 (prune node_modules, .worktrees) -name .mcp.json | grep -l 7890: 27 of 31",
      "find ... -path '*/.codex/config.toml' | grep -l 7890: 5 of 13 (Dopemux-ChatRipperXXX, _worktrees/pr92-legacy-primary-independent-019, adOps, dopeClaw, dopemux-mvp)",
      ".mcp.json hits (paths relative to ~/code, 27): ./ChatRipperXXX/.mcp.json ./Dopemux-ChatRipperXXX/.mcp.json ./_worktrees/pr92-legacy-primary-independent-019/.mcp.json ./adOps/.mcp.json ./claude-mem/.mcp.json ./dNh_CRM.restore-review-20261021/files/.mcp.json ./dNh_CRM/.mcp.json ./dNh_CRM__audit-argon-pr289/.mcp.json ./dNh_CRM__audit-argon-pr291/.mcp.json ./dNh_CRM__audit-argon-pr292/.mcp.json ./dNh_CRM__claude-config-audit-fixes-20261016/.mcp.json ./dNh_CRM__config-successor/.mcp.json ./dNh_CRM__fix-sdist-uv013/.mcp.json ./dNh_CRM__prompt-audit-2026-10-18/.mcp.json ./dNh_CRM__sdist-successor/.mcp.json ./djdom-generator/.mcp.json ./dnh-crm/.mcp.json ./dopeClaw/.mcp.json ./dopemux-main/.mcp.json ./dopemux-model-intel/.mcp.json ./dopemux-mvp-archaeology-supervisor-001/.mcp.json ./dopemux-mvp-batch02-dmx-1418-upload-artifact-v6/.mcp.json ./dopemux-mvp-dcp-routing-fasttrack-001/.mcp.json ./dopemux-mvp-remote-host-read-001/.mcp.json ./dopemux-mvp/.mcp.json ./dopemux-r6-routing/.mcp.json ./openclaw_marketplace_agent_docs/.mcp.json",
      "global grep -q 7890: ~/.claude.json, ~/.codex/config.toml, ~/.commandcode/mcp.json hit; ~/.claude/settings.json, ~/.claude/settings.local.json, ~/.config/opencode/opencode.jsonc, ~/.copilot/mcp-config.json, ~/.gemini/settings.json, ~/.gemini/antigravity/mcp_config.json do not"
    ],
    "red_lane": [
      "src/dopemux/dcp/red_lane_rules.py:84-86",
      ".claude/hooks/dcp_surface_guard.py (RED_LANE_ID DCP-RED-MERGE-SEAM-0001); src/dopemux/claude/native_hooks.py:446-448",
      "tests/test_dcp_surface_guard.py:211-221",
      "tools/pr_steward/security_release_gate.py:56-82 (dcp_boundary)",
      "docs/90-adr/adr-224-dcp-workflow-seam-narrow-carveout.md; adr-226-dope-context-seam-narrow-carveout.md (precedents)"
    ],
    "workstream_go": [
      "W01/W02 NO_GO: red_lane evidence; W05 NO_GO: orchestrator_v4 evidence; W03 GO: no existing dopemux auth group (rg), src/dopemux/auth and commands/auth_commands.py absent",
      "W04/W06/W07/W08 GO_REDUCED: see reductions"
    ],
    "q12_ports": [
      "services/registry.yaml: conport-http 3004, conport-mcp 3005, dope-memory 3020, task-orchestrator 8000 (Python service)",
      "mcp_catalog.yaml servers conport (sse, CONPORT_MCP_PORT 3005), dope-memory (http, DOPE_MEMORY_PORT 3020), task-orchestrator (http, TASK_ORCHESTRATOR_HTTP_PORT 7890 reserved)",
      "git show 9bbb4f853:tests/arch/test_service_port_drift.py (PR #1485 content, unmerged; EXCEPTIONS has task-orchestrator)"
    ]
  }
}
```
