# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — aggregate return (pre-freeze)

**Authority:** NONE. This aggregate preserves each child's state and subject; it does not mint PASS, READY or DONE. **Branch:** `feat/runner-memory-2a`, local only, never pushed. **Base:** `97b6d5040` (origin/main has since moved to `6fb9d8179` with #1482). **Head at writing:** `eb3e43934`. **Audit:** NOT_RUN (the single final independent L3 audit is held for J04-FREEZE; route not yet chosen).

## Workstreams

| WS | Work | Child status | Commit | Record |
|---|---|---|---|---|
| W09 | ADR-227 red-lane carve-out (20 files) | READY_FOR_AUDIT | `95c54c4ec` (+ test fix `de88645d1`) | ADR227_ACCEPTANCE.md |
| W01 | dope-memory write identity, auth modes, principal column | READY_FOR_AUDIT | `52d5b5f8d` | W01_RETURN.md |
| W02 | ConPort write identity, streamable surface, migration 008 | NEEDS_SUPERVISOR → resolved | `baac57244` | W02_RETURN.md |
| W06 | Local writers record self-asserted principals | INCOMPLETE → resolved | `e9418771d` | W06_RETURN.md |
| W10 | ADR-227 Amendment 1, Dockerfile COPY lines, CI test fix | READY_FOR_AUDIT (1 correction) | `9e1b3df38` | W10_RETURN.md |
| W03 | `dopemux auth` and the keychain helper | READY_FOR_AUDIT | `27d8caa82` | W03_RETURN.md |
| W04 | Stdio bridge with token and id filling | READY_FOR_AUDIT (1 correction) | `7675468a7` | W04_RETURN.md |
| W05 | 11 internal HTTP callers send their principal's token | READY_FOR_AUDIT | `302675efa` | W05_RETURN.md |
| W07 | Codex config behind the gate; catalog | NEEDS_SUPERVISOR → READY_FOR_AUDIT (1 correction, 1 follow-up) | `29203f1eb`, `f88e99dcd` | W07_RETURN.md |
| W08 | How-to, ADR-MCPINT-002 amendment draft, agent docs | READY_FOR_AUDIT | `05c1def3e` | (this file) |
| W12 | Servers fill omitted ids from their binding | NEEDS_SUPERVISOR → READY_FOR_AUDIT (1 correction) | `d314f2141` | W12_RETURN.md |

Test fixes the team lead made in workstreams' own test directories:
- `de88645d1` (W09): ADR status
- `7f8b9ed9b` (W01): sidecar test
- `fe5e3db28` (W01): capture principal

Every child was Sonnet. Structural counts found zero advisor calls and zero subagents in every child.

## Operator rulings recorded

| Record | Words | Effect |
|---|---|---|
| AUTHORIZATION_RECORD.md | "Approve and authorize" | R2 design rev 2 and W01-W09 |
| ADR227_ACCEPTANCE.md | "Accept ADR-227" | J01-CARVEOUT |
| KEYCHAIN_ACL_RESULT.md | (procedure run; "yyeess" for the Claude Code read) | default ACL |
| AMENDMENT_01.md | "Yes, extend 2A" | W10: Dockerfiles exempted, COPY lines, CI test |
| AMENDMENT_02.md | "Later, with 2B (Recommended)"; "Yes, add the guard (Recommended)" | Claude Code stays on direct HTTP (G5 to 2B); suite-wide keychain guard |
| AMENDMENT_03.md | "Allow log mode (Recommended)" | Codex gate accepts `log` or `enforce` |
| AMENDMENT_04.md (+ addendum) | "Default to the binding (Recommended)" | W12: omitted ids filled from the binding |

### Design deviations from 2A revision 2

| Item | Change | Record |
|---|---|---|
| G1 | "reject a write without workspace_id" becomes "never store a write under any workspace but the server's own" | Amendment 04 |
| G5 | Claude Code on the bridge moves to Wave 2B | Amendment 02 |
| 5.7 | gate check 1 accepts `log` or `enforce` | Amendment 03 |
| Carve-out | 22 exempt files instead of 20 | Amendment 01 |

## Validation at this head (team lead)

| Set | Result |
|---|---|
| Whole 2A set, services venv (all W suites, guard, wiring, hooks, MCP config, catalog and arch contracts, repair, capture, ledgers, endpoint, lifecycle, caller suites, `tests/pr_steward`, `tests/dcp`) | 2,066 passed, 1 deselected |
| Deselected | `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`: it diffs `.github/workflows/` from an old packet base and fails on main too. No 2A commit touches `.github/`. |
| Red-lane scanner and PR gate tests | included above (`tests/dcp`, `tests/pr_steward`) |
| Live servers, real keychain, image builds, migrations, the live Codex run | NOT_RUN |

## Open for the operator

**Before the audit:**
- Update the branch from main (`6fb9d8179` or later).
- Choose the final audit route. The route must be a different model family from the Claude implementers.

**After the audit:**
- push and draft PR
- signing
- the ADR-MCPINT-002 amendment's acceptance

**Operator steps in the how-to (`docs/02-how-to/runner-memory-identity.md`):**
1. delete the keychain probe item;
2. issue tokens (`runner:codex`, `internal:cli`, `internal:adhd`);
3. rebuild and restart the memory sidecars (whether `dopemux mcp start` rebuilds is UNKNOWN);
4. run ConPort migration 008 (psql, then adopt);
5. `dopemux mcp generate --agent-matrix --apply --output-dir <dir>` for Codex;
6. the live Codex acceptance run.

**`enforce`, not available in 2A:**
- container callers cannot reach the keychain;
- container ids are unknown (weaker since W12);
- the bridge's progress route drops `instance_id`;
- Claude Code is on direct HTTP until 2B;
- other writers remain (task-orchestrator, `pm/adapters/conport.py`, `services/dope-memory/mcp_stdio_adapter.py`).

## Residual risks carried to the audit

From the W returns:
1. Bare `python` in rendered Codex entries.
2. Codex and Claude Code stdio working directory is UNKNOWN.
3. No `security` exit-44 observation.
4. No token caching.
5. Helper duplicated across 11 callers.
6. `released_only=False` defaults.
7. `/health` is unauthenticated and checked only at generation time.
8. The conftest guard does not cover `services/*/tests`.
9. Pre-existing breakage in `claude_brain` and `ddg_mcp_stdio.py` imports.
10. Stale `services/dope-memory/mcp_stdio_adapter.py`.
