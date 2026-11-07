---
id: rfc-2026-10-30-runner-memory-parity-2a
title: Runner Memory Parity, Wave 2A - Verified Identity for the Memory Spine, Codex First
type: rfc
status: draft
author: claude-code
date: '2026-10-30'
created: 2026-10-30
updated: 2026-10-31
last_review: '2026-10-31'
next_review: '2027-01-29'
owner: '@hu3mann'
derived_from:
- docs/90-adr/adr-mcpint-002-agent-exposure-and-read-plane.md (gate G1 preconditions)
- task-packets/DMX-MEMSPINE-IDENTITY-005.json
- proof/MACRO-DMX-RUNNER-MEMORY-2A-001/review_bundle/W00_FINDINGS.md (revision 2 inputs)
- proof/MACRO-DMX-RUNNER-MEMORY-2A-001/review_bundle/OPERATOR_RULINGS_R2.md
prelude: Revision 2 design for giving every agent runner verified, attributable access to the dopemux memory servers (dope-memory and ConPort), Codex first. Per-request identity on HTTP writes, one keychain-held bearer token per runner, a runner-neutral stdio route, and a narrow red-lane carve-out. The task orchestrator moves to a later wave.
summary: Wave 2A revision 2 unlocks dope-memory and ConPort for Codex with verified identity on every HTTP write and moves Claude Code onto the same model. The task orchestrator (4.0.0 is unreleased upstream) moves to Wave 2C. Wave 2B (other runners' renderers, an installed-config doctor, the read-only facade, hook parity) follows.
---
# Runner Memory Parity, Wave 2A (revision 2)

Status: **draft, for operator approval.** Nothing is built until this revision is approved. Revision 1 (sha256 `1fea6013…`, commit `77b4052f7`) was approved on 2026-10-31 and is superseded: its read-only investigation (W0) found facts that change the design, and the operator ruled on them the same day. Facts are from `origin/main` at `97b6d5040`, from this machine and from W0's findings (`W00_FINDINGS.md`, sha256 `4baa2184…`) unless a line says otherwise.

## 0. What the operator decided

Quoted from chat:

- 2026-10-30. Build for every runner: "make sure we are building for all cli and desktop runners. claude code is the primary target, but codex is the main implementer and grok, agy, cmd code, and opencode (as well as copilot cli) get a fair bit of use too". Scope: "Yes, that scope". Identity strength: "Require verified identity". ADR change: "Amend it (Recommended)".
- 2026-10-31, after W0 (`OPERATOR_RULINGS_R2.md`):
  - DCP red lane: "Narrow carve-out ADR (Recommended)".
  - Task orchestrator: "Split it out (Recommended)". Upstream has no 4.0.0 release (latest `v3.16.0`), and 4.0 removes every 3.x tool this repo calls.
  - G2 scope: "HTTP writes only (Recommended)".
- Revision 1's decisions about the orchestrator ("upgrade conport to 4.0.0" read as the orchestrator; "All at once" cutover) move with the orchestrator to Wave 2C and are not used here.

## 1. Why

Codex does most of the implementation and cannot reach the memory layer:

- `ADR-MCPINT-002` gives Codex the full MCP fleet only after per-request memory identity with fail-closed writes (`DMX-MEMSPINE-IDENTITY-005`) and authenticated orchestrator actors. Neither exists.
- dope-memory takes `workspace_id`/`instance_id` from process env with defaults (`dope_memory_main.py:57-58`, `mcp_http.py:115-116`). ConPort treats a missing `instance_id` as shared (`instance_detector.py:52-78`). The incident behind the ADR (writes filed under another repo's workspace) can still happen.
- No ConPort or dope-memory route checks who is calling. ConPort's REST port (container 3004) is published on host loopback, and its SSE proxy forwards to REST with no credentials (`server.py:55-205`).

## 2. Scope split

- **Wave 2A (this design):** verified identity on HTTP writes to **dope-memory and ConPort**, the token tooling, the runner-neutral stdio route, a narrow red-lane carve-out, and generated config for **Codex** and **Claude Code** for those two servers. Acceptance: a live Codex session reads and writes both as `runner:codex`.
- **Wave 2B (later):** renderers for Grok, AGY and Command Code; OpenCode and Copilot renderer fixes; the installed-config doctor; the DCP read-only facade; hook parity.
- **Wave 2C (later, new):** the task orchestrator: upstream 4.0.0 once released, its token auth and strict config, the migration of the 3.x tool surface this repo calls (W0 counted 24 files under `.claude/` plus manifests, policy tables and tests), and the cross-repo `:7890` cutover (27 repo `.mcp.json`, 5 `.codex/config.toml`, 3 global configs). Until 2C, Codex gets no orchestrator entry.

## 3. Goals

| ID | Goal | Done when |
|---|---|---|
| G1 | Memory writes carry identity or fail. | dope-memory and ConPort reject an HTTP write without `workspace_id`, and without `instance_id` where the stored row carries one (5.1); tests prove it and run in CI. |
| G2 | Every **HTTP** write to dope-memory and ConPort carries a verified principal. | Once a server is in `enforce` mode, an HTTP write without a valid token is rejected; the verified principal is stored on the write. Local writers that touch the ledger file or Redis directly are recorded as self-asserted internal principals (5.3). |
| G3 | Runners get tokens without tokens entering a tracked file. | `dopemux auth issue <runner>` stores a token in the macOS keychain and writes its hash to the host hash directory; tracked files only reference it. |
| G4 | Codex reaches dope-memory and ConPort through generated config. | `dopemux mcp generate --apply` writes Codex's entries only when the gate holds (5.7); a live Codex session reads and writes both as `runner:codex`. |
| G5 | Claude Code keeps working on the same identity model. | Claude Code's config (produced by `dopemux mcp init`/`ensure`) uses the same route with `runner:claude`; its memory calls still work. |
| G6 | The red-lane exception is explicit and minimal. | An ADR (status proposed until the operator accepts it) and a `red_lane_rules.py` change exempt exactly the files the workstreams name; every other path stays blocked; tests prove both. |
| G7 | The ADR and agent docs match. | An ADR-MCPINT-002 amendment (status proposed) and agent-doc entries describe the new model, including that the orchestrator stays gated until 2C. |

## 4. Non-goals

- Everything in Wave 2B and Wave 2C. The orchestrator wrappers, config, hooks and tool surface are not changed.
- The Python task-orchestrator service on `:8000` (it writes ConPort REST without credentials; see 5.5).
- The full ConPort CRS v2 gateway.
- Per-agent identity inside a runner; remote or multi-host deployment.
- New instance columns on ConPort tables that have none today (5.1).

## 5. Decisions

Each is the supervisor's call unless section 0 quotes the operator.

### 5.1 Identity model

- **Principal = runner** (`runner:claude`, `runner:codex`; 2B adds the rest) **or internal caller** (`internal:hooks`, `internal:cli`, `internal:wma`, `internal:bridge-proxy`, `internal:dopecon`, `internal:adhd`, `internal:brain`). One token per principal, valid on both memory servers.
- **Workspace and instance are request data, not identity.** `workspace_id` is required on every HTTP write. `instance_id` is required where the stored row carries one: dope-memory writes, and ConPort `workspace_contexts` and `progress_entries`. ConPort `decisions` keep `created_by_instance`; `custom_data` has no instance column (W0, `schema.sql:33-47, 109-118`) and none is added in 2A.
- **Two sources must agree.** The stdio route fills `workspace_id`/`instance_id` from the caller's repo (its `.envrc.dopemux-mcp`); each server is bound to its workspace by its own env. A write whose `workspace_id` does not match the server's binding is rejected.
- **Writes means every mutating route** (W0's list, larger than revision 1's): dope-memory's 10 MCP tools' write paths and `POST /tools/*`; ConPort `POST /api/decisions`, `/api/progress`, `/api/custom_data`, `/api/custom_data/claim`, `/api/context/{ws}`, `/api/instance/fork`, `/api/progress/promote`, `/api/progress/promote_all`, `PUT /api/progress/{id}`, `DELETE /api/custom_data`, and `POST /mcp` `tools/call` for every write tool.
- **ConPort shared data** (supervisor's call): an `instance_id` of `shared` lands where `NULL` lands today; existing `NULL` rows read as `shared`; no row is rewritten.
- **dope-memory stays one container per worktree.** Sidecar env (auth mode, hash-directory mount) comes from the generated compose override in `src/dopemux/mcp/docker_runtime.py:161-203`, not `compose.yml`; `generate_mcp_env` drops keys containing `TOKEN` or `PASSWORD`, so only the mode and the directory path travel through env.

### 5.2 Tokens

- `dopemux auth issue|rotate|revoke <principal>` and `list` (principals and dates, never tokens). Writes are dry-run by default and need `--apply`.
- A token is 32 random bytes, base64url, in the macOS keychain (generic password, service `dopemux-mcp`, account = principal).
- Servers hold only SHA-256 hashes, in one file under `~/.config/dopemux/auth/` (outside every repo, mode 0600 in a 0700 directory), mounted **as a directory**, read-only, into the containers (a single-file bind mount may not survive an atomic replace). The orchestrator's token format (YAML with `id`, `token_sha256`, `capabilities`) is 2C's.
- Keychain reads must not prompt on every launch. W0 wrote the operator procedure to test the item ACL; it runs before W3 is dispatched, and its result sets the helper's ACL choice.

### 5.3 Getting tokens to runners and internal callers

- **The stdio route** (`src/dopemux/mcp/http_stdio_bridge.py`, extended): resolve the server's port from the caller repo's `.envrc.dopemux-mcp` (read only `*_PORT` keys with the existing `safe_port_int`; the file also exports a database password); read the principal's token from the keychain through the W3 helper; send `Authorization: Bearer` on every request; speak streamable HTTP (W0: `Accept: application/json, text/event-stream`, echo `mcp-session-id`, parse SSE-framed and plain JSON responses, print nothing for `notifications/initialized`); fail closed.
- **A worktree without `.envrc.dopemux-mcp` fails closed** with an instruction to run `dopemux mcp init` there. Falling back to the main checkout's file would bind the worktree to the wrong containers.
- Codex and Claude Code both use the stdio route for both memory servers.
- **HTTP internal callers** send their own principal's token through the W3 helper (W0 counted about 15 ConPort REST writers plus `pm/adapters/dope_memory.py`). ConPort's own SSE proxy (`server.py`) and stdio proxy (`conport_mcp_stdio.py`) forward the caller's token to REST, or `internal:bridge-proxy`'s when the caller has none and the server is in `log` mode.
- **Local writers are self-asserted** (operator ruling): `capture_client.py` (writes the SQLite ledger and applies its migrations), `native_hooks.py` (Redis `XADD`) and `eventbus_consumer.py` (ledger writes from Redis) record a principal such as `internal:hooks` with a `self_asserted` marker. They carry no token and are not part of G2.

### 5.4 ConPort transport

W0 confirmed revision 1's open branch: the REST `POST /mcp` surface answers `initialize` with `-32601`, lists 13 prefixed tools and lacks four. **ConPort adds `FastMCP.streamable_http_app()` (mcp 1.29) on the existing SSE listener beside `sse_app()`**, exposing the same 17 tool names Claude Code sees today. Authentication covers the REST port, the SSE surface and the new streamable surface; auth on the MCP surfaces alone would leave the REST data plane open.

### 5.5 Rollout without cutting anyone off

- Each memory server gets an auth mode: `off` (today), `log` (accept everything; store the verified principal or `unverified`; count unverified calls by caller), `enforce` (reject unverified HTTP writes with 401). Deploy in `log`; `dopemux mcp doctor` reports any server left in `log` and the unverified callers it has seen.
- `enforce` is switched on per server only after a Claude Code and Codex smoke test through the stdio route passes, and after `log` mode shows no unverified writer the operator has not accepted.
- **Known unverified writers that must be fixed or accepted before ConPort `enforce`:** the Python task-orchestrator service (`services/task-orchestrator`, red lane, non-goal) and anything W0 marked UNKNOWN (`pm/adapters/conport.py` posting to `/kg/custom_data`). The how-to lists them.

### 5.6 Red-lane carve-out (operator ruling)

`DCP-RED-MERGE-SEAM-0001` (`src/dopemux/dcp/red_lane_rules.py:84-86`, and `:44` for `services/dopecon-bridge/`) hard-blocks Claude Code edits under `services/working-memory-assistant/`, `docker/mcp-servers-source/conport/` and `services/dopecon-bridge/`, and PR Steward marks such PRs `dcp_boundary`. A new ADR in the ADR-224/226 pattern exempts **exactly the files named in the W1, W2 and W5 write allowlists**, as file-exact negative lookaheads (no directory exemption, so no traversal companion is needed). Every other path under those trees stays blocked; `red_lane_scanner.py` content rules still apply. The operator accepts the ADR before W1, W2 or W5 is dispatched.

### 5.7 Generator gate

`--allow-sequenced` is replaced by checks run before writing a write-capable Codex config for the memory servers:

1. dope-memory and ConPort health report `enforce` and identity-required writes (capability fields added in W1 and W2);
2. a token for the target runner exists in the keychain.

If either fails, the generator writes the preview only and names the failed check. **Released:** dope-memory and ConPort through the stdio route. **Not released:** the task orchestrator (until 2C), serena, dope-context, gpt-researcher, pal-stdio. Gate text and tests that name `actor_authentication.enabled` (`mcp_commands.py:1100`, `fleet_catalog.py:306, 1195`, `tests/unit/test_mcp_commands_catalog.py:516`) are reworded. `mcp_catalog.yaml` and `src/dopemux/mcp/default_catalog.yaml` are byte-identical and change together.

### 5.8 Schema changes and migrations

- dope-memory's SQLite ledger migrates automatically on first use (`chronicle/store.py:103-116`, `sqlite_migrations.py:74`), by the server or by `capture_client.py` from any hook process. The principal column is added as a new file under `chronicle/migrations/` plus `chronicle/schema.sql`: nullable, default `unverified`. Whichever process touches the ledger first applies it; a nullable column keeps older readers working.
- ConPort's principal column goes through `migrations/` and `conport_migration_gate.py` (extend `REQUIRED_MIGRATIONS` if the gate requires it) and runs only as an operator step, never on container start. The known migration-gate deadlock on a fresh database and its workaround (psql, then adopt) go in the how-to.
- Each migration has a rollback (drop the column; rows written in `log` mode keep their data).

### 5.9 ADR

ADR-MCPINT-002 is amended (operator decision): for the memory servers, "verified per-runner transport identity on HTTP writes, with identity-required writes" replaces the actor-auth precondition, restated as G1 plus G2. The orchestrator precondition stays in force and is re-expressed in Wave 2C. The operator accepts the amendment before the Codex config ships.

## 6. Security

- **Protects against:** one runner writing as another over HTTP; writes filed under the wrong workspace or instance; an untokened HTTP writer once a server is in `enforce`.
- **Does not protect against:** a compromised runner using its own token; another process of the same macOS user reading the keychain item or the ledger file; local writers forging their self-asserted principal; a hostile host process.
- Tokens: keychain only; hashes on servers; constant-time comparison; never logged; rotation and revocation by command.
- Servers stay on `127.0.0.1`. Anything left in `log` is visible in `dopemux mcp doctor`.

## 7. Workstreams (proposed for R2)

| ID | Work | Writes (indicative) |
|---|---|---|
| W0 | Done in R1; its findings are evidence for R2 and are not re-run. | — |
| W1 | dope-memory: required ids on HTTP writes, binding check, auth modes, principal column, health capability; the CI-run endpoint test updated; `eventbus_consumer.py` records its self-asserted principal. | the W1 file list in the carve-out ADR; `src/dopemux/mcp/docker_runtime.py`; tests |
| W2 | ConPort: required ids where rows carry them, binding check, auth on REST, SSE and the new streamable surface, `shared`, principal column and migration, the two in-image proxies forward tokens. | the W2 file list in the carve-out ADR; `src/dopemux/mcp/docker_runtime.py`; tests |
| W3 | `dopemux auth` and the shared keychain/hash helper. | `src/dopemux/commands/auth_commands.py`, `src/dopemux/auth/`, `src/dopemux/cli.py`, tests |
| W4 | Stdio bridge per 5.3. | `src/dopemux/mcp/http_stdio_bridge.py`, tests |
| W5 | ConPort and dope-memory HTTP internal callers send their principal's token (the ~15 W0 listed, including the two `services/dopecon-bridge/` files under the carve-out). | the files W0 listed; tests |
| W6 | Local writers record self-asserted principals (`capture_client.py`, `native_hooks.py`). | those two files; tests |
| W7 | Generator: Codex config for the two memory servers via the stdio route, the real gate (5.7), catalog and Claude Code `init`/`ensure` rendering. | `src/dopemux/mcp/fleet_catalog.py`, `src/dopemux/commands/mcp_commands.py`, `mcp_catalog.yaml`, `src/dopemux/mcp/default_catalog.yaml`, tests |
| W8 | Docs: how-to (operator steps in order, each with its rollback), agent docs, ADR-MCPINT-002 amendment draft. | `docs/`, `AGENTS.md`, `.claude/claude.md` |
| W9 | The red-lane carve-out: ADR draft (status proposed), `red_lane_rules.py` file-exact exemptions, guard tests. | `docs/90-adr/`, `src/dopemux/dcp/red_lane_rules.py`, `tests/test_dcp_surface_guard.py` |

Order: W9 first, then the operator accepts its ADR. W3 and W4 do not touch red-lane paths and may run before that acceptance. W1 and W2 follow acceptance; W5 needs W1, W2 and W3; W6 needs W1; W7 needs W1-W4; W8 is last.

## 8. Constraints

- Governance: one MacroPacket revision (R2), one final independent audit after freeze. Lane L3 (red-lane rules, compose override, catalog, hooks).
- New tests go under `tests/unit/`. CI also runs `services/working-memory-assistant/tests/test_mcp_http_endpoint.py` (`ci-complete.yml:195-199`); W1 updates it. Tests at the `tests/` root (`test_dcp_surface_guard.py`, `test_mcp_config_generation.py`) are not run by CI and must also be run explicitly.
- CI runs Python 3.12.13. Foundations Wave 1's port-drift test (PR #1485) must stay green.
- Merge order: after #1482, #1483, #1485 and #1484.
- Writes to the user's home directory (keychain, `~/.config/dopemux/auth/`, global runner configs) happen only through explicit operator-run commands with a dry run first.

## 9. Operator steps still ahead

Accepting the carve-out ADR; running the keychain ACL procedure; approving this revision and R2; issuing tokens; running the ConPort migration; switching each server to `enforce` after the smoke test; accepting the ADR-MCPINT-002 amendment; approving the audit route; the live Codex acceptance run.

## 10. Left to the builder

Exact middleware placement in each server; the health capability field names; error wording; the bridge's config discovery details; test layout.
