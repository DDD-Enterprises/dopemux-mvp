# W02 return — TP-DMX-RUNNERMEM2A-R2-W02-CONPORT-IDENTITY-001

**Child status:** NEEDS_SUPERVISOR (code complete; blockers outside its write surface). **Team lead disposition:** committed as `baac57244` after one diff re-read; W01 test follow-up `7f8b9ed9b`. The image-build blocker below is open and goes to the operator. Audit: NOT_RUN (held for J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W02_EXECUTION_BINDING.json` (sha256 `3bce75bd9986083eb59bfeb7f1d0d493b81b8c144b974c2e67669cc30fc69a1c`), `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 206 assistant turns (harness record) |
| Duration / tokens / tool uses | 1,230 s / 359,006 / 131 (caps 150 min / 1.8M / 350) |
| Attempts | 1 (no retry) |
| advisor calls / subagents | 0 / 0 (structural count: Bash 36, Read 22, Write 15, Edit 57, SubagentHandback 1) |
| Guard denials | 0 |
| Edits through Bash | 0 (the dispatch note was followed; two `cd /dev/null` no-ops, cwd unaffected) |

## Write surface (C12)

20 paths before commit, all inside the W02 write_surface (`OUTSIDE_SURFACE: none`).

## Validation (team lead re-ran)

| Command | Exit | Bucket |
|---|---|---|
| verify line, worktree `.venv` (`--extra test`) | 0 | PASS: 177 passed, 2 skipped (`mcp` absent: `test_mcp_surfaces.py`, `test_stdio_proxy.py` NOT_RUN in this venv) |
| verify line, services venv | 0 | PASS: 225 passed |
| W01 + W02 + W09 + guard + ConPort wiring + dope-memory endpoint + capture client + MCP lifecycle, services venv | 1 → 0 | FAIL before the follow-up (W01's `test_should_leave_the_conport_service_untouched` pinned the opposite of W02 B06); after `7f8b9ed9b`: 604 passed |
| `git diff --check` | 0 | PASS |
| pre-commit on all W02 files (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN) |
| TDD failing-first (child) | 1 | recorded: 141 failed, 38 passed, 42 errors before production code |
| Mutation check (child) | 1 | disabling forwarding and the enforce gate failed 36 tests; restored |
| Live image, Postgres, migration | — | NOT_RUN (C10) |

## Facts for later workstreams

| For | Fact |
|---|---|
| W03 | Same hash file and format as dope-memory (`memory-token-hashes.json`, constants byte-identical to `services/working-memory-assistant/auth_identity.py`). `PROXY_TOKEN_PROVIDER` in `server.py:31` and `conport_mcp_stdio.py:28` defaults to `lambda: None`; W03's helper cannot run inside the container (no keychain), so the `internal:bridge-proxy` fallback stays unset unless a later packet decides how it gets a token. |
| W04 | ConPort binding is `DOPEMUX_WORKSPACE_ID` (set by the sidecar override); the stdio caller token is `CONPORT_STDIO_TOKEN`. Streamable HTTP is `POST /mcp` on the MCP listener (container :3005), beside `/sse`. |
| W05 | Every write needs `workspace_id` equal to the server binding; `instance_id` for context and progress writes. `fork_instance` now takes a required `target_instance`; `update_progress` and `promote` gained required `workspace_id`/`instance_id`. |
| W07 | REST `GET :3004/health` (200 body only): `auth_mode`, `identity_required_writes`, `auth_hash_file`, `auth_unverified_calls`, `auth_principal_column` (`ok`/`partial`/`missing`). Env: `CONPORT_AUTH_MODE`, `CONPORT_AUTH_DIR`. |
| W08 | Migration 008: psql `-v ON_ERROR_STOP=1 -f migrations/008_write_principal.sql`, then `DPMX_CONPORT_MIGRATION_APPLY=1 python migrations/conport_migration_gate.py apply` (adopts 008 without running it), then `verify`, then `auth_principal_column == "ok"`. Rollback: set mode to off/log, run `008_rollback.sql`, `DELETE FROM conport_schema_migrations WHERE version = 8;`. Enforce returns 503 on writes while the column is missing. `migrations/README.md` still lists up to 007. |

## Open items

1. **Neither rebuilt image would start (operator decision).** Both Dockerfiles copy modules one by one, and neither copies the new `auth_identity.py`:
   - `docker/mcp-servers-source/conport/Dockerfile:30-38` (W02; imported unguarded by `enhanced_server.py`, `server.py`, `conport_mcp_stdio.py`)
   - `services/working-memory-assistant/Dockerfile.dope-memory:47-51` (W01, found by the team lead while checking W02's report; imported unguarded by `dope_memory_main.py` and `mcp_http.py`)

   Both Dockerfiles are red-lane paths that ADR-227 does not exempt, and no R2 write surface lists them. The design missed them. Clearing it needs the operator to amend ADR-227 with two more file-exact exemptions and extend a write surface, then one `COPY` line per Dockerfile. Until then, do not rebuild either image from this branch.
2. **Deploy order.** Id validation applies in every auth mode, so any ConPort or dope-memory writer that omits the ids gets 400 once the new images run. W05 covers the 11 known HTTP writers (the child's report wrongly said W05 covers only the two dopecon-bridge files); W05 B03 lists further writers as blockers before enforce. The images must not deploy before W05 lands.
3. **Binding variables differ by server.** dope-memory binds to `DOPE_MEMORY_WORKSPACE_ID` (worktree directory name); ConPort binds to `DOPEMUX_WORKSPACE_ID` (`identity.workspace_id or worktree_root`, `lifecycle.py:1221`). A caller that sends one workspace string to both servers may be rejected by one of them. W04 must send each server its own binding value; J02 checks it.
4. **Direct HTTP MCP clients** (W01 residual 1) now applies to ConPort too: write tools gained required ids, which changes the schemas Claude Code sees.
5. Smaller notes from the child, recorded for the audit: `_log_progress` now stores the request's instance (it stored NULL before); `_log_decision` now writes `created_by_instance`; `update_context` URL-quotes the workspace id; unverified counts can double for `custom_data` writes through REST `/mcp`; the forwarded-caller header is trusted for counting only when the request authenticated as `internal:bridge-proxy`; `direct_server.py` (legacy, not in the image) still defines unauthenticated write routes.
