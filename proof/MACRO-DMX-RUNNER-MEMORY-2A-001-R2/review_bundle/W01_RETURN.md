# W01 return — TP-DMX-RUNNERMEM2A-R2-W01-DOPE-MEMORY-IDENTITY-001

**Child status:** READY_FOR_AUDIT. **Team lead disposition:** committed as `52d5b5f8d` after one diff re-read; no correction round. Audit: NOT_RUN (held for the single final L3 audit at J04-FREEZE).

## Route and counters

| Field | Value |
|---|---|
| Binding | `W01_EXECUTION_BINDING.json` (sha256 `41eb6ab4afa6ebf3d651b9889bac9a55b9f7001e1f3f5c9fa078c50ad29be7bb`), `ct validate-binding` PASS |
| Requested route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Observed model | `claude-sonnet-5-5` on all 214 assistant turns of the child transcript (harness record, not a provider attestation) |
| Duration / tokens / tool uses | 990 s / 278,331 / 81 (caps 120 min / 1.5M / 300) |
| Attempts | 1 (no retry) |
| advisor calls | 0 (structural count of `tool_use` blocks: Bash 60, Read 13, Write 7, SubagentHandback 1; the two `advisor` strings in the transcript are tool definitions in the request shape) |
| Subagents spawned | 0 |
| Guard denials | 0 (all 9 `DCP-RED-MERGE-SEAM` strings are context: CLAUDE.md, packet, design, a test failure message) |

## Write surface (C12)

`git status --porcelain` before commit: 8 modified + 10 new paths, all inside the write_surface (`OUTSIDE_SURFACE: none`). The red-lane hook did not fire for these paths (ADR227_ACCEPTANCE.md, enforcement note), so this check is the enforcement.

Process deviations, no effect on the result:

- The child edited existing files through Bash-run Python, not the Edit tool, so no PreToolUse Edit hook saw them. No hook denied anything first, so C12's "never work around the guard" was not engaged. Later red-lane workstreams are told to use Edit/Write.
- The child ran `cd /tmp` in some commands despite the dispatch note. The team-lead session's cwd stayed `/Users/hue/code/dopemux-mvp` (checked after the return).

## Validation (team lead re-ran each)

| Command | Exit | Bucket |
|---|---|---|
| commit.verify pytest line as written (worktree `.venv`, `--extra test`) | 0 | PASS: 129 passed, 2 skipped (no `fastmcp`: `test_mcp_writes.py`, `test_mcp_http_endpoint.py`) |
| same with `--extra services` (scratchpad venv from the frozen lock) | 0 | PASS: 173 passed |
| `test_mcp_http_endpoint.py --maxfail=1 --no-cov` (CI style) | 0 | PASS: 9 passed |
| `tests/unit/runner_memory_2a_r2_w09/ tests/test_dcp_surface_guard.py` | 1 → 0 | FAIL at `175a01a4d` (2 tests pinned ADR status `proposed`), fixed by the team lead in `de88645d1`; 196 passed |
| `git diff --check` | 0 | PASS |
| pre-commit on all 18 files (`SKIP=markdownlint`) | 0 | PASS (markdownlint NOT_RUN: Node 27.0.0-alpha install fails) |
| TDD failing-first run (child) | 1 | recorded by the child: 19 failed, 1 passed, 3 collection errors before production code |
| Child-only: WMA regression set, WMA unit tests, MCP lifecycle/launcher/ledger/env/doctor suites | 0 | PASS per child; 15 pre-existing failures identical before and after; not re-run by the team lead |
| pyright | — | NOT_RUN |

The packet's verify line under-tests W01 without `--extra services`. The final audit and W07 should run with it.

## Interpretation accepted (C08)

B01 says the env defaults "are removed". W01 removed them for writes only; reads default to the bound workspace. Design G1 and section 5.1 (rev 2, lines 54 and 77) require ids on HTTP **writes**, so this matches the design.

## Facts later workstreams must use

| For | Fact | Where |
|---|---|---|
| W02, W03 | Hash file `$DOPE_MEMORY_AUTH_DIR/memory-token-hashes.json`, JSON object `{"<lowercase hex sha256 of the UTF-8 token>": "<principal>"}`; principals match `^(runner\|internal):[a-z0-9][a-z0-9_.-]{0,63}$`; re-read on mtime/size change | `auth_identity.py:45-50, 69` |
| W04 | The server binding is `DOPE_MEMORY_WORKSPACE_ID` (set per worktree by `lifecycle.py:1226-1228`, child's reading, not re-verified); the bridge must send that exact value as `workspace_id` | `dope_memory_main.py` `BOUND_WORKSPACE_ID` |
| W07 | Health gate: `auth_mode == "enforce"` and `identity_required_writes is True`; also `auth_hash_file` (`ok`/`missing`/`invalid`/`unconfigured`) and `auth_unverified_calls` | `auth_identity.py:248-258` |
| W08 | The sidecar mounts `~/.config/dopemux/auth` read-only only if it exists when the override is generated; after the first token is issued the sidecar needs a restart | `docker_runtime.py` `generate_compose_override` |

## Residual risks (for J02 and the final audit)

1. **Direct HTTP MCP clients must now supply the exact bound `workspace_id` and an `instance_id` on writes.** The design says the stdio route fills them (rev 2 line 78). It does not say how a client that talks to dope-memory over HTTP directly (Claude Code's `http` entry) learns the bound value. Until W04/W07 answer this, such writes fail with a 400 or a ToolError.
2. `WriteAuthMiddleware` buffers every `POST /mcp` body in all modes; bodies over 4 MiB get 413 even in `off` and `log`.
3. `/health` is unauthenticated and now lists caller labels (User-Agent, up to 64 characters, at most 100 callers).
4. The idempotent `ADD COLUMN` guard in `sqlite_migrations.py` applies to every migration file, not only v1.3.0 (it only makes older migrations more tolerant).
5. Not covered by W01: `trajectory_state` upserts carry no principal; `capture_client.py` rows stay `unverified` until W06; `wma_mcp/server.py` (red lane, not exempt, not wired to HTTP) does not accept `write_principal`.
