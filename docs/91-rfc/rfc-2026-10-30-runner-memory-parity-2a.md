---
id: rfc-2026-10-30-runner-memory-parity-2a
title: Runner Memory Parity, Wave 2A - Verified Identity for the Memory Spine and Task Orchestrator, Codex First
type: rfc
status: draft
author: claude-code
date: '2026-10-30'
created: 2026-10-30
updated: 2026-10-30
last_review: '2026-10-30'
next_review: '2027-01-28'
owner: '@hu3mann'
derived_from:
- docs/90-adr/adr-mcpint-002-agent-exposure-and-read-plane.md (gate G1 preconditions)
- task-packets/DMX-MEMSPINE-IDENTITY-005.json
- runner mapping and recon of origin/main at 97b6d5040 on 2026-10-30
prelude: Design for giving every agent runner verified, attributable access to the dopemux memory servers and task orchestrator, starting with Codex. Per-request identity on memory writes, one bearer token per runner verified by the servers, the task orchestrator upgraded to upstream 4.0.0, and generated runner configs.
summary: Wave 2A unlocks ConPort, dope-memory and the task orchestrator for Codex with verified identity, and moves Claude Code onto the same model. Wave 2B (other runners' renderers, an installed-config doctor, the read-only facade, hook parity) follows.
---
# Runner Memory Parity, Wave 2A

Status: **draft, for operator approval.** Nothing is built until this is approved. Facts are from `origin/main` at `97b6d5040` and from this machine on 2026-10-30, unless a line says otherwise.

## 0. What the operator decided

Quoted from chat on 2026-10-30:

- Build for every runner: "make sure we are building for all cli and desktop runners. claude code is the primary target, but codex is the main implementer and grok, agy, cmd code, and opencode (as well as copilot cli) get a fair bit of use too".
- Scope: "Yes, that scope", in answer to "Should the next wave be unlocking memory for Codex and the other runners?"
- Identity strength: "Require verified identity", in answer to "Is self-asserted agent attribution enough for Codex writes?"
- "upgrade conport to 4.0.0". **Read as: upgrade the task orchestrator to upstream 4.0.0.** ConPort is in-repo code with no version line; 4.0.0 is the task-orchestrator release that moved identity to per-client bearer tokens. The operator confirms or corrects this reading when approving.
- ConPort's shared-data mode was asked and not answered. Section 5 records the supervisor's call.

## 1. Why

Codex does most of the implementation and cannot reach the memory layer:

- `ADR-MCPINT-002` (accepted 2026-07-17) gives Codex the full MCP fleet only after two preconditions: per-request memory identity with fail-closed writes (`DMX-MEMSPINE-IDENTITY-005`), and authenticated actors on the task orchestrator (`actor_authentication.enabled`).
- Neither exists. `dope-memory` takes `workspace_id`/`instance_id` from process env with defaults (`services/working-memory-assistant/dope_memory_main.py:57-58`, `mcp_http.py:110-116`). ConPort takes `instance_id` from env and treats a missing one as shared (`docker/mcp-servers-source/conport/instance_detector.py:52-78`). The incident that motivated the ADR (writes filed under another repo's workspace id) can still happen.
- The orchestrator's actor check is a client-side hook that tests whether an `actor` field is present (`.claude/hooks/orchestrator_enforcement.py:117-149`). Nothing verifies who the actor is, and only Claude Code and Codex run the hook.
- The generator's gate is a bare flag: `dopemux mcp generate --allow-sequenced` checks neither precondition (`src/dopemux/commands/mcp_commands.py:1079`).

Other runners have the same problem in smaller form: AGY reaches no dopemux server; OpenCode and Copilot CLI have hand-edited configs with wrong ports (OpenCode dope-memory `:3035`, Copilot task-orchestrator `:8000`).

## 2. Scope split

**Wave 2A (this design):** verified identity on the three write-capable servers (dope-memory, ConPort, task orchestrator), the token tooling, a runner-neutral stdio route, and generated config for **Codex** and **Claude Code**. Acceptance is a live Codex session that reads and writes all three with its own verified identity.

**Wave 2B (later, separate design):** renderers for Grok, AGY and Command Code; fixes to the OpenCode and Copilot renderers; a doctor that compares each installed runner config with the catalog; the DCP read-only facade; hook parity for runners that support hooks. Wave 2A builds the pieces 2B reuses (tokens, the stdio route).

## 3. Goals

| ID | Goal | Done when |
|---|---|---|
| G1 | Memory writes carry identity or fail. | dope-memory and ConPort reject a write without `workspace_id` and `instance_id`; tests prove it and run in CI. |
| G2 | Every call to the three servers carries a verified runner identity. | A call without a valid token is rejected once a server is in `enforce` mode; the verified principal is stored on every write. |
| G3 | Runners get tokens without tokens ever entering a tracked file. | `dopemux auth issue <runner>` creates a token in the macOS keychain and registers its hash with the servers. Tracked configs only reference it. |
| G4 | Codex reaches all three servers through generated config. | `dopemux mcp generate --apply` writes Codex's MCP config only when the preconditions hold; a live Codex session reads and writes all three as `runner:codex`. |
| G5 | Claude Code keeps working, on the same identity model. | Claude Code's generated config sends `runner:claude`'s token; its memory and orchestrator calls still work. |
| G6 | The task orchestrator runs upstream 4.0.0 with token auth. | The image pin is 4.0.0, auth uses per-runner tokens, and the repo's hooks no longer demand an `actor` field. |
| G7 | The ADR and agent docs match. | An ADR-MCPINT-002 amendment (status proposed) and agent-doc entries describe the new model. |

## 4. Non-goals

- Everything listed under Wave 2B.
- The Python task-orchestrator FastAPI service on `:8000`.
- The full ConPort CRS v2 gateway (`docs/90-adr/adr-conport-canonical-record-service-v2.md`). Wave 2A delivers the subset ADR-MCPINT-002 needs.
- Per-agent identity inside a runner (subagents of Codex share `runner:codex`).
- Remote or multi-host deployment. Everything stays on `127.0.0.1`.

## 5. Decisions

Each is the supervisor's call unless section 0 quotes the operator.

### 5.1 Identity model

- **Principal = runner.** One bearer token per runner: `runner:claude`, `runner:codex`, and in 2B `runner:opencode`, `runner:copilot`, `runner:grok`, `runner:agy`, `runner:commandcode`. The same token is valid on all three servers, so a runner has one principal everywhere.
- **Workspace and instance are request data, not identity.** They become required arguments on memory writes (G1). The principal says who wrote; workspace and instance say where.
- **ConPort shared data** (unanswered question, supervisor's call): keep shared data as an explicit instance named `shared`. A write with no `instance_id` is rejected; a write with `instance_id: "shared"` lands where `NULL` lands today. Existing `NULL` rows are read as `shared`; no row is rewritten in this wave.

### 5.2 Tokens

- `dopemux auth` (new command group): `issue <runner>`, `rotate <runner>`, `revoke <runner>`, `list` (principals and creation dates, never tokens).
- A token is 32 random bytes, base64url. It is stored in the macOS keychain (generic password, service `dopemux-mcp`, account `<runner>`).
- Servers hold only SHA-256 hashes, in a host file outside every repo (`~/.config/dopemux/auth/`), mounted read-only into the containers. The orchestrator's 4.0.0 token file format is written in whatever shape 4.0.0 requires (to be confirmed in W0).
- Tracked files never contain a token. `.envrc.dopemux-mcp` (gitignored) may export a token by reading the keychain at shell start; it never stores one.

### 5.3 Getting tokens to runners: the stdio route

- Every runner on the list can launch a stdio MCP server; not all can send HTTP headers or expand env vars in URLs. So the default route for non-Claude runners is the existing stdio bridge, `src/dopemux/mcp/http_stdio_bridge.py`, extended to:
  - resolve the server's base URL from the repo's `.envrc.dopemux-mcp` (per-worktree ports), found by walking up from the working directory;
  - read the runner's token from the keychain at launch and send `Authorization: Bearer …` on every request;
  - fail with a clear stderr message when either is missing, instead of sending an unauthenticated request.
- Codex uses this route in 2A. (Codex can also send a bearer token itself through `bearer_token_env_var`; the stdio route is chosen because it also solves per-worktree ports and ConPort's transport, below.)
- Claude Code keeps its direct HTTP/SSE entries in `.mcp.json` and adds an `Authorization` header that references an env var exported by `.envrc.dopemux-mcp`.

### 5.4 ConPort transport

- Codex cannot speak SSE. ConPort's SSE surface is on `:3005`; its REST child already answers plain JSON-RPC `POST /mcp` on `:3004` (`enhanced_server.py:276`), which is what the stdio bridge expects.
- W0 checks that the `:3004` JSON-RPC surface exposes the same tools as the SSE surface. If it does, the bridge targets `:3004`. If not, W2 adds a streamable-HTTP app beside `sse_app()` in `server.py`, and the bridge targets that.
- Authentication applies to every ConPort surface that serves tools (`:3004` and `:3005`).

### 5.5 Rollout without cutting anyone off

- **Memory servers** (in-repo code) get an auth mode setting: `off` (today), `log` (accept everything; store the verified principal or `unverified`; count unverified calls), `enforce` (reject unverified calls). Deploy in `log`, migrate configs, then switch to `enforce`. `log` is time-boxed: `dopemux mcp doctor` reports any server left in `log` mode.
- **Task orchestrator 4.0.0:** whether it has a permissive phase is unknown until W0. If it has none, the upgrade cutover must happen together with every affected config getting a token (see 5.6).
- **Hooks:** `orchestrator_enforcement.py` and `native_hooks.py:438-444` currently require an `actor` field; 4.0.0 reportedly refuses one. W5 changes them in the same change as the upgrade so they stop requiring it (and, if confirmed, flag its presence).

### 5.6 Cross-repo reach

The task orchestrator on `:7890` is one container for the whole machine. About 25 repos' `.mcp.json` files, four repos' `.codex/config.toml`, and the global Claude, Codex and Command Code configs point at it. The running container is currently serving dNh_CRM. Requiring tokens affects all of them. **This is an operator decision** (section 9); the design assumes the cutover touches only configs that `dopemux` generates and leaves other repos to re-run `dopemux mcp init`, unless the operator chooses otherwise.

### 5.7 Generator gate becomes real

`--allow-sequenced` is replaced by checks the generator runs before writing a write-capable Codex config:

1. dope-memory and ConPort report auth mode `enforce` and identity-required writes (a version/capability probe on their health endpoints, added in W1 and W2);
2. the orchestrator reports token auth on (4.0.0 config);
3. a token for the target runner exists in the keychain.

If any check fails, the generator writes the preview only and prints which check failed.

### 5.8 ADR

ADR-MCPINT-002's precondition 2 names `actor_authentication.enabled`, a 3.x setting that 4.0.0 removed. W7 drafts an amendment (status proposed): "verified per-runner transport identity on all write-capable servers" replaces precondition 2, and precondition 1 is restated as G1 plus G2. **Accepting the amendment is an operator decision** (section 9).

## 6. Security

- **Protects against:** one runner writing as another; writes filed under the wrong workspace or instance; a runner with no token writing at all once servers are in `enforce`.
- **Does not protect against:** a compromised runner using its own token; anything else running as the same macOS user reading the keychain item or calling the servers with a stolen token; a hostile process on the host.
- Tokens: keychain only; hashes on servers; constant-time comparison; never logged (log the principal, never the header); rotate and revoke by command.
- Servers stay bound to `127.0.0.1`.
- Anything left in `log` mode is visible in `dopemux mcp doctor`.

## 7. Workstreams (proposed)

| ID | Work | Writes (indicative) |
|---|---|---|
| W0 | Verify the unknowns before code: pull the 4.0.0 image; read its real changelog and auth docs; confirm `API_AUTH_MODE`, the token file format, whether a body `actor` is refused, whether a permissive mode exists, where its SQLite lives and whether 3.8 to 4.0 migrates it (rollback needs a backup); confirm ConPort `:3004` tool parity with `:3005`; confirm keychain reads from the bridge do not prompt every launch. | none (a findings record under `proof/`) |
| W1 | dope-memory: required `workspace_id`/`instance_id` on writes, per-workspace ledger path, env defaults removed, auth middleware with modes, principal stored on writes. | `services/working-memory-assistant/`, `compose.yml` (its env), tests under `tests/` |
| W2 | ConPort: required `instance_id` on writes with the explicit `shared` instance, auth middleware on `:3004` and `:3005`, transport per 5.4. | `docker/mcp-servers-source/conport/`, `compose.yml` (its env), tests under `tests/` |
| W3 | `dopemux auth` command group and the host hash files. | `src/dopemux/commands/auth_commands.py`, `src/dopemux/cli.py`, tests |
| W4 | Stdio bridge: envrc port resolution, keychain token, fail-closed. | `src/dopemux/mcp/http_stdio_bridge.py`, tests |
| W5 | Task orchestrator 4.0.0: image pin, config migration, token auth, hooks changed in the same change, backup and rollback steps. | `scripts/mcp-wrappers/task-orchestrator-*.sh`, `.taskorchestrator/config.yaml`, `.claude/hooks/orchestrator_enforcement.py`, `src/dopemux/claude/native_hooks.py`, tests |
| W6 | Generator: Codex config through the stdio route, Claude `.mcp.json` headers, the real gate (5.7); catalog updates. | `src/dopemux/mcp/fleet_catalog.py`, `src/dopemux/commands/mcp_commands.py`, `mcp_catalog.yaml`, `src/dopemux/mcp/default_catalog.yaml`, schemas if needed, tests |
| W7 | Docs, agent docs, ADR amendment draft; live acceptance run with Codex (operator-run). | `docs/`, `AGENTS.md`, `.claude/claude.md`, ADR amendment |

Order: W0 first. W1, W2, W3 and W4 are independent of each other after W0. W5 needs W3 (tokens). W6 needs W1-W5. W7 last.

## 8. Constraints

- Governance: one MacroPacket, one final independent audit after freeze. Expect lane L3: `compose.yml`, hooks, `mcp_catalog.yaml` and `.mcp.json` are contract-sensitive surfaces. The audit route is operator-approved per run.
- New tests go under `tests/` (CI runs `tests/unit`, `tests/arch`, `tests/dcp`, `tests/integration`); `services/*/tests` and `docker/*/tests` are not run by CI.
- CI runs Python 3.12.13 (`.python-version`).
- Foundations Wave 1's port-drift test (PR #1485) checks catalog/registry/compose consistency; any port or catalog change here must keep it green.
- Merge order: this joins the signed-proof merge train after #1482, #1483, #1485 and #1484.
- Writing to the user's home directory (keychain, `~/.config/dopemux/auth/`, global runner configs) changes persistent configuration: every such write is an explicit command the operator runs, with a dry run first.

## 9. Open operator decisions

1. **Cross-repo cutover** (5.6): accept that requiring tokens on the shared orchestrator affects every repo pointing at `:7890`, with other repos re-running `dopemux mcp init`; or require a per-repo opt-in; or keep the orchestrator permissive until a separate cutover.
2. **ADR-MCPINT-002 amendment** (5.8): accept that verified per-runner transport identity replaces `actor_authentication.enabled` as precondition 2.
3. **Reading of "upgrade conport to 4.0.0"** (section 0).

## 10. Left to the builder

Exact middleware placement in each server; the health-endpoint capability field names; error message wording; the bridge's config-discovery details; test layout.
