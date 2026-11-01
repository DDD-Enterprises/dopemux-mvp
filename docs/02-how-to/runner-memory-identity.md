---
id: runner-memory-identity
title: Verified Runner Identity for dope-memory and ConPort (Wave 2A Operator Steps)
type: how-to
owner: '@hu3mann'
date: 2026-11-01
author: '@hu3mann'
last_review: '2026-11-01'
next_review: '2027-02-01'
prelude: Ordered operator steps for Wave 2A runner memory identity on dope-memory and ConPort, each with its rollback and a done or ahead mark. Covers keychain tokens, image rebuild, migrations, Codex config, log mode and how to read unverified writers from /health. States plainly that enforce mode is not available in 2A.
---
# Verified Runner Identity for dope-memory and ConPort (Wave 2A)

This guide lists every operator step for Wave 2A (`MACRO-DMX-RUNNER-MEMORY-2A-001-R2`) in
order. Each step names its rollback and says whether it is **done** or **still ahead**.
Design: `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` (revision 2). Evidence:
`proof/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/review_bundle/` (`W01_RETURN.md` to `W07_RETURN.md`,
`W10_RETURN.md`, `AMENDMENT_01.md` to `AMENDMENT_03.md`).

Nothing below has been run live. Every live behaviour is `NOT_RUN` until you run the step
and read the result.

## What Wave 2A does and does not do

Does:

- dope-memory and ConPort reject an HTTP write without `workspace_id` (and `instance_id`
  where the row carries one), in every auth mode (`W02_RETURN.md` open item 2).
- Each server has an auth mode: `off`, `log` or `enforce`. The sidecar default is `log`
  (`src/dopemux/mcp/docker_runtime.py:154-179`, `services/working-memory-assistant/auth_identity.py:46`).
  In `log` mode a request with a valid token is stored with its verified principal; every
  other write is accepted, stored as `unverified` and counted by caller.
- `dopemux auth` issues one keychain-held token per principal; the servers hold only
  SHA-256 hashes (`src/dopemux/commands/auth_commands.py`).
- Codex reaches both servers through the stdio bridge as `runner:codex` once a gate holds
  (step 8).

Does not (not built in 2A):

- **`enforce` is not available in 2A.** See the section "Why enforce is blocked" below.
- **`dopemux mcp doctor` does not show unverified writers.** The design (5.5) asked for
  that report. It was not built: `mcp_doctor_cmd` in
  `src/dopemux/commands/mcp_commands.py` reads no auth field. Use each server's `/health`
  instead (step 9).
- **Claude Code is not moved to the bridge.** It keeps its direct HTTP entries; its move is
  Wave 2B (`AMENDMENT_02.md`). A Claude bridge renderer exists
  (`_render_claude_memory_bridge_entry`, `mcp_commands.py:648`) but nothing calls it.
- **The task orchestrator is not covered.** Its token auth and the actor-auth precondition
  move to Wave 2C. Grok, AGY, Command Code, OpenCode and Copilot renderers are Wave 2B.

## Step list

| # | Step | State |
|---|---|---|
| 1 | ADR-227 accepted | done 2026-10-31 |
| 2 | Keychain ACL procedure | done 2026-11-01 (default ACL); delete the probe item still ahead |
| 3 | `dopemux auth issue` per principal | ahead |
| 4 | Rebuild and restart the memory sidecars | ahead |
| 5 | dope-memory ledger migration (auto-applies) | ahead |
| 6 | ConPort migration 008 | ahead |
| 7 | `dopemux mcp init` in each worktree | ahead |
| 8 | Codex config: `dopemux mcp generate --agent-matrix --apply` | ahead |
| 9 | Log-mode period: read `/health`, accept or fix each unverified writer | ahead |
| 10 | Live Codex acceptance run | ahead |
| 11 | Enforce | future, blocked |

## Step 1. ADR-227 accepted (done)

ADR-227 exempts 22 named files from the DCP red lane so Wave 2A could edit them (20 files
plus the two Dockerfiles added by Amendment 1). The operator accepted it on 2026-10-31
(`ADR227_ACCEPTANCE.md`); Amendment 1 followed under "Yes, extend 2A" (`AMENDMENT_01.md`).

Rollback: `git revert` the W10 commit restores the 20-file set; `git revert` the W09 commit
restores the three blanket patterns (`docs/90-adr/adr-227-memory-spine-seam-narrow-carveout.md`,
Migration Strategy and Amendment 1).

## Step 2. Keychain ACL procedure (done; one cleanup ahead)

Run on 2026-10-31 local (2026-11-01 UTC). Result in `KEYCHAIN_ACL_RESULT.md`: an item
created with the **default ACL** (no `-T`, no `-A`) was read without a prompt from the
Claude desktop terminal pane, the Codex shell tool and the Claude Code Bash tool, with the
login keychain unlocked. A locked keychain, a session with no GUI (`ssh localhost`, a
`launchd` agent) and the ACL variants were not run (`NOT_RUN`). The helper treats any
nonzero exit, timeout or empty output as a hard failure and never retries into a prompt
(`KEYCHAIN_ACL_RESULT.md`, "Decision for W03").

Still ahead, operator: delete the throwaway probe item.

```bash
security delete-generic-password -s dopemux-mcp-probe -a probe
```

Rollback: none needed; the probe item is not a real token.

## Step 3. Issue tokens (ahead)

Every `dopemux auth` command that writes is a dry run until you add `--apply`. No command
prints a token or a hash (`auth_commands.py` module docstring). Tokens go to the macOS
keychain (service `dopemux-mcp`, account = principal); hashes go to
`~/.config/dopemux/auth/memory-token-hashes.json` (directory 0700, file 0600).

Principals to issue in 2A:

| Principal | Used by | Source |
|---|---|---|
| `runner:codex` | Codex, through the stdio bridge | `W07_RETURN.md` |
| `internal:cli` | host callers: `pm/adapters/dope_memory.py`, `tools/conport_client.py`, `instance_state.py`, `profile_analytics.py`, `commands/decisions_commands.py` | `W05_RETURN.md`, "Per caller" |
| `internal:adhd` | host caller `adhd/rte_adapter.py` | `W05_RETURN.md`, "Per caller" |

`runner:claude` is not needed in 2A, because Claude Code stays on direct HTTP. The
container callers' principals (`internal:adhd` for `services/adhd_engine`, `internal:brain`,
`internal:dopecon`) cannot be used from a container: the images have no
`/usr/bin/security` (`W05_RETURN.md` open item 2). `internal:hooks` and `internal:wma` are
self-asserted by local writers and carry no token (`W06_RETURN.md`).

```bash
dopemux auth issue runner:codex            # dry run: prints the plan
dopemux auth issue runner:codex --apply
dopemux auth issue internal:cli --apply
dopemux auth issue internal:adhd --apply
dopemux auth list                          # principals and dates, never tokens
```

The first real run of the keychain write and the exit-44 "not found" handling has not been
exercised (`W03_RETURN.md`: `NOT_RUN`, UNKNOWN until this step).

`issue` writes the keychain, then the hash file, then a date-only sidecar. A failure partway
leaves a state that re-running the command repairs (`W03_RETURN.md`, "Notes for the audit").

The sidecar only mounts the auth directory if `~/.config/dopemux/auth` exists when the
compose override is generated (`docker_runtime.py:196-203, 211-219`). This step creates it,
so run it before step 4. If a sidecar was already running before the first `issue`, restart
it (step 4).

Rollback: `dopemux auth revoke <principal> --apply` removes the hash, the metadata and the
keychain item (`auth_commands.py`, `revoke`). `dopemux auth rotate <principal> --apply`
replaces a token if one is suspected.

## Step 4. Rebuild and restart the memory sidecars (ahead)

Both images must be rebuilt before the new servers run. Both Dockerfiles now `COPY` the new
`auth_identity.py` (`services/working-memory-assistant/Dockerfile.dope-memory:48`,
`docker/mcp-servers-source/conport/Dockerfile:32`; `W10_RETURN.md`). The image build and
start themselves are `NOT_RUN`; the only evidence is a static COPY-versus-import test.

Start through `dopemux mcp start` only. Never run raw `docker compose up` or `docker run`
(AGENTS.md section 12.6).

Two facts to check, because the repo does not settle them:

- **How the rebuild happens is UNKNOWN.** `compose_up_command`
  (`src/dopemux/mcp/docker_runtime.py:356-382`) runs `up -d --no-deps` with no `--build`,
  so `dopemux mcp start` alone may reuse an existing image. Decide the sanctioned rebuild
  route before relying on this step.
- **Check the result from `/health`.** A rebuilt server reports `auth_mode`
  (step 9). A server that still runs the old image has no such field.

Deploy order: id validation applies in every auth mode, so any writer that omits
`workspace_id` or `instance_id` gets a 400 once the new images run (`W02_RETURN.md` open
item 2). The 11 HTTP writers in the repo were changed in W05 to send ids when they have
them. Host callers need `.envrc.dopemux-mcp` loaded (for example through direnv), or
`instance_id` is omitted and the server returns 400 (`W05_RETURN.md` open item 6).

**Claude Code consequence in 2A.** Claude Code's direct HTTP entry does not fill the ids.
After the rebuild, its dope-memory and ConPort writes need the exact bound `workspace_id`
and an `instance_id` in the tool call, or they fail with a 400 or a tool error
(`W01_RETURN.md` residual 1; `W02_RETURN.md` open item 4; `W04_RETURN.md` ruling 2: "Direct
HTTP clients are unaffected"). The bridge fixes this only for runners on the bridge
(Codex in 2A). Whether Claude Code's model supplies the ids unprompted is UNKNOWN.

Rollback: restart on the previous images. Record the current image ids before the rebuild.
Nothing else changes in this step.

## Step 5. dope-memory ledger migration (ahead; auto-applies)

Migration `services/working-memory-assistant/chronicle/migrations/v1_3_0_add_write_principal.sql`
adds `write_principal` (default `unverified`) and `write_principal_self_asserted` to
`raw_activity_events`, `work_log_entries`, `issue_links` and `reflection_cards`. It applies
on first use by whichever process opens the ledger first: the server or `capture_client.py`
from a hook. Existing rows read as `unverified`; nothing is rewritten. The ledger is
`<repo>/.dopemux/chronicle.sqlite`
(`services/working-memory-assistant/canonical_ledger.py:10, 84-90`).

Rollback: the `-- ROLLBACK:` lines in the migration header, one statement per line, then
restart the writers on the previous code. They need SQLite 3.35 or later for `DROP COLUMN`.
The last line deletes the `v1.3.0` row from `schema_migrations`.

## Step 6. ConPort migration 008 (ahead; operator-run)

`docker/mcp-servers-source/conport/migrations/008_write_principal.sql` adds a nullable
`write_principal` column (default `unverified`) to `workspace_contexts`, `decisions`,
`progress_entries` and `custom_data`. It never runs on container start. Run one pass per
ConPort database in use.

The gate's own `apply` self-deadlocks on a fresh database, so apply by hand first, then
adopt (`W02_RETURN.md`, "Facts for later workstreams", W08 row; the migration header):

```bash
psql -v ON_ERROR_STOP=1 -d "$DATABASE_URL" -f docker/mcp-servers-source/conport/migrations/008_write_principal.sql
DPMX_CONPORT_MIGRATION_APPLY=1 python docker/mcp-servers-source/conport/migrations/conport_migration_gate.py apply   # adopts 008, runs no SQL
python docker/mcp-servers-source/conport/migrations/conport_migration_gate.py verify
```

Then read ConPort's `/health`: `auth_principal_column` must be `ok` (`partial` and `missing`
are the other values). The URL comes from your install; this guide does not read or print
credentials. Until the column exists, `log` and `off` modes keep writing without it
and `enforce` would answer writes with 503 (migration header).
`migrations/README.md` still lists migrations only up to 007.

Rollback (`008_rollback.sql` header):

1. Set `CONPORT_AUTH_MODE` to `off` or `log` first (step 11 shows how).
2. Run `008_rollback.sql`. It drops the four columns; rows keep their other data.
3. `DELETE FROM conport_schema_migrations WHERE version = 8;`

## Step 7. `dopemux mcp init` in each worktree (ahead)

```bash
dopemux mcp init
source .envrc.dopemux-mcp && dopemux mcp doctor
```

Claude Code stays on direct HTTP: `init` and `ensure` render the same entries as before
and the tracked `.mcp.json` is unchanged (`AMENDMENT_02.md`; `mcp_commands.py:623-631`).
This step also writes the ports and ids the bridge reads from `.envrc.dopemux-mcp`
(`W04_RETURN.md`). A worktree with no `.envrc.dopemux-mcp` makes the bridge fail closed and
tell you to run this step.

Rollback: unchanged from before Wave 2A; `init` is not a new command.

## Step 8. Codex config (ahead)

Before this step the operator accepts the ADR-MCPINT-002 amendment
(`docs/90-adr/adr-mcpint-002-amendment-runner-identity.md`, status `proposed` today;
design 5.9 requires acceptance before the Codex config ships).

The gate (`evaluate_codex_memory_gate`, `mcp_commands.py`; `AMENDMENT_03.md`) passes when:

1. For both dope-memory and ConPort, `/health` reports `auth_mode` of `log` or `enforce`
   and `identity_required_writes` true; ConPort also reports `auth_principal_column` `ok`.
   `off` fails.
2. A keychain token exists for `runner:codex` (the value is discarded unread).

```bash
dopemux mcp generate --agent-matrix                         # dry run
dopemux mcp generate --agent-matrix --apply --output-dir <dir>
```

`--apply` requires `--output-dir` (`mcp_commands.py`, `generate`: "--apply requires
--output-dir to bound generated writes"). The shorthand without it fails.

- When the gate holds, `.codex/config.toml` gets a marker-delimited managed region
  (`# BEGIN dopemux-managed mcp_servers` to `# END ...`) with the `conport` and
  `dope-memory` bridge entries; your other keys are kept. Hand-written
  `[mcp_servers.*]` tables outside the markers abort the merge.
- When it fails, only the preview under `--output-dir` is written, and each failed check is
  named.
- In `log` mode the apply prints a notice: Codex's writes are verified as `runner:codex`;
  writers without a token are still accepted and recorded `unverified` until `enforce`.
- Side effect: `--apply` also rewrites `opencode.jsonc` (its managed `mcp` section) and
  `mcp-proxy-config.copilot.yaml` in the repo (`_apply_in_repo_agent_configs`). Review the
  diff.

Requirements and unknowns (`W07_RETURN.md`, residual risks):

- The entry starts the bridge with bare `python`. That interpreter must have `dopemux`
  installed; if not, the server does not start (fails closed). Check:
  `python -c "import dopemux.mcp.http_stdio_bridge"`.
- The working directory Codex gives an MCP server is **UNKNOWN** until the live run (step 10).
  The bridge finds `.envrc.dopemux-mcp` by walking up from its working directory and has no
  `--workdir` option.
- The gate reads `/health` at generation time only. If `enforce` is switched off later,
  nothing re-checks.

Rollback: `.codex/config.toml` is tracked, so `git checkout -- .codex/config.toml`
restores it, or delete the managed region between the two marker lines. The command makes
no backup of its own. Review the other in-repo files it touched.

## Step 9. Log-mode period (ahead)

While the servers run in `log`, read each server's `/health` and decide, for every unverified
caller, whether to fix it or accept it. `dopemux mcp doctor` does not report this.

| Server | Port key in `.envrc.dopemux-mcp` | Route |
|---|---|---|
| dope-memory | `DOPE_MEMORY_PORT` | `GET http://127.0.0.1:<port>/health` |
| ConPort | `CONPORT_HTTP_PORT` (the REST port; not `CONPORT_MCP_PORT`) | `GET http://127.0.0.1:<port>/health` |

Fields (`services/working-memory-assistant/auth_identity.py:248-258`,
`docker/mcp-servers-source/conport/auth_identity.py:284-294`,
`docker/mcp-servers-source/conport/enhanced_server.py:544-545`;
`mcp_commands.py` `_MEMORY_HEALTH_TARGETS` for the ports):

| Field | Meaning |
|---|---|
| `auth_mode` | `off`, `log` or `enforce` |
| `identity_required_writes` | always `true` in the new images |
| `auth_hash_file` | `ok`, `missing`, `invalid` or `unconfigured` |
| `auth_unverified_calls` | map of caller label to count of writes accepted without a verified token |
| `auth_principal_column` | ConPort only: `ok`, `partial` or `missing` |

Reading `auth_unverified_calls`:

- Nothing is counted in `off` mode (`authorize_write` returns early). A request with a wrong
  token counts as unverified too.
- The caller label is the request's User-Agent (up to 64 characters), else the client
  host. At most 100 labels are tracked; the rest go under `other`
  (`auth_identity.py:64-66, 106-107, 220-229`). `/health` is unauthenticated and lists these
  labels (`W01_RETURN.md` residual 3).
- ConPort trusts the forwarded-caller header for counting only when the request
  authenticated as `internal:bridge-proxy` (`W02_RETURN.md` open item 5). Counts for
  `custom_data` writes through REST `/mcp` can double.

Known unverified writers to fix or accept (`W05_RETURN.md` open items 2 to 5; design 5.5):

| Writer | Why unverified | Notes |
|---|---|---|
| `adhd_engine`, `claude_brain`, `dopecon-bridge` (containers) | no keychain in the image | needs a decision: host-side proxy, a read-only token mount, or moving the writes to the host |
| ConPort's own proxy fallback (`internal:bridge-proxy`) | `PROXY_TOKEN_PROVIDER` defaults to `lambda: None` | same gap |
| `services/task-orchestrator` (Python service) | writes ConPort REST without credentials | red lane, non-goal in 2A |
| `src/dopemux/pm/adapters/conport.py` | works only if `CONPORT_URL` points at the bridge; sends `workspace_id: "default"` | |
| `services/dope-memory/mcp_stdio_adapter.py` | stale adapter listed in `config/runtime_authority_manifest.json` | |
| Claude Code (direct HTTP) | no token until Wave 2B | see step 4 for the id consequence |
| dopecon-bridge `update_context` PATCH | ConPort answers 405 | |
| Local writers (`capture_client.py`, `native_hooks.py`, `eventbus_consumer.py`) | no token by design | recorded as self-asserted `internal:*`, not part of the token model (`W06_RETURN.md`) |

Rollback: none; reading `/health` changes nothing.

## Step 10. Live Codex acceptance (ahead)

Pass condition: a Codex session reads and writes both servers, and the stored principal is
`runner:codex`.

1. Start Codex in the checkout and confirm it lists the `conport` and `dope-memory` tools.
   This also settles the working-directory unknown from step 8.
2. Make one write to each server through Codex.
3. Read the stored principal back:
   - dope-memory: query `<repo>/.dopemux/chronicle.sqlite`, for example
     `SELECT write_principal, write_principal_self_asserted FROM work_log_entries ORDER BY ts_utc DESC LIMIT 5;`
     (columns from `chronicle/schema.sql:84-86`).
   - ConPort: `SELECT write_principal FROM decisions ORDER BY created_at DESC LIMIT 5;` (or
     the table you wrote to; `docker/mcp-servers-source/conport/schema.sql:34-46`), through
     the `psql` route used in step 6.
4. Check that `auth_unverified_calls` did not gain a Codex caller label.

There is no automated smoke test. Design 5.5 asked for a Claude Code and Codex smoke test
before `enforce`; none was built in 2A, and this step is the manual equivalent for Codex.
Claude Code is not part of it in 2A.

Rollback: revoke the token (`dopemux auth revoke runner:codex --apply`) and restore
`.codex/config.toml` (step 8). Rows already written keep their stored principal.

## Step 11. Enforce (future; blocked)

### Why enforce is blocked in 2A

`enforce` rejects an HTTP write that carries no valid token (401). In 2A these still write
without one:

1. **Container callers cannot reach the keychain.** `adhd_engine`, `claude_brain` and
   `dopecon-bridge` have no `/usr/bin/security` (`W05_RETURN.md` open item 2).
2. **Container ids are unknown.** The compose entries for dopecon-bridge and adhd-engine set
   no `DOPEMUX_WORKSPACE_ID` or `DOPEMUX_INSTANCE_ID`, and the bridge defaults to a
   hardcoded path (`W05_RETURN.md` open item 3).
3. **The bridge's progress route drops `instance_id`.** `ProgressRequest` in
   `services/dopecon-bridge/dopecon_bridge/routes.py:112-122` has no such field; the file is
   red lane and not exempt (`W05_RETURN.md` open item 4).
4. **Claude Code is on direct HTTP until Wave 2B**, so its writes carry no token
   (`AMENDMENT_02.md`).
5. **Other writers:** `services/task-orchestrator`, `pm/adapters/conport.py`,
   `services/dope-memory/mcp_stdio_adapter.py` (`W05_RETURN.md` open item 5).

Design 5.5 also requires a smoke test and a review of accepted writers before `enforce`
(`AMENDMENT_03.md`, "Design deviation").

### How it would be switched (future step only, do not run in 2A)

The sidecar override reads the mode from the environment of the process that runs
`dopemux mcp start`, per server: `DOPE_MEMORY_AUTH_MODE` for dope-memory and
`CONPORT_AUTH_MODE` for ConPort; unset means `log`
(`docker_runtime.py:154-179`; `lifecycle.py:1241-1249` passes no other source). They are
switched separately. Set one to `enforce`, then restart that sidecar through
`dopemux mcp start`. Whether a plain start recreates a running container to apply a changed
override is UNKNOWN; confirm from `/health` that `auth_mode` reads `enforce`. Switch ConPort
only after step 6 reports `auth_principal_column` `ok`, or its writes answer 503.

To switch back: set the same variable to `log` (or `off`) and restart the same way; confirm
`auth_mode` on `/health`. Rows already stored keep their principal.
