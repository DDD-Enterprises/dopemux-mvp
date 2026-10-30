# RETURN-01 — MACRO-DMX-MEMORY-BRIDGE-001-R2 (aggregate, authority NONE)

**Status**: `READY_FOR_AUDIT` for W02, W03, W04 (each committed); the single final independent L2 audit is `NOT_RUN` (operator-gated route, no audit line sent).
**Content head (frozen subject)**: `52855fb35ea40f420bdacdcab9e092f8d15292c6` on `claude/memory-bridge-001-b349d8`; base `93050d135ffc2592000c1d0edef82b2912935525`. A proof-only commit follows it.
**Authorization**: `AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R2_EXECUTION=YES`, relayed verbatim (see `../../MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/AUTHORIZATION_RECORD.md`).

## Commits

| Commit | Workstream | Files |
|---|---|---|
| `ed53a0c74` | evidence | flat proof copies of the R1 package, `W01_FINDINGS.md`, authorization record, R2 package |
| `e561166a6` | W02 | plugin.json, hooks.json, register.tsx, register.test.ts, README.md |
| `1ce149a76` | W03 (incl. 1 correction round) | register.tsx, register.test.ts, README.md |
| `52855fb35` | W04 | docs/02-how-to/memory-bridge.md |

## Route and measured counters against the PROPOSED allowances

Counters are from each completion notice (`subagent_tokens`, `tool_uses`, `duration_ms`). Active (model-working) time is not recordable: UNKNOWN. The W03 correction was a resume of the same agent; its notice is added to the first run (the sum may over-count if the harness reports cumulative tokens).

| WS | Requested | Observed (transcript `message.model`) | Tokens | Tool uses | Elapsed | Cap (tokens / tools / elapsed) | Attempts | advisor / Agent calls (transcript) |
|---|---|---|---|---|---|---|---|---|
| W01 (R1, outside the R2 budget) | claude-sonnet-5-5 | claude-sonnet-5-5 | 335,949 | 123 | 815.8 s | n/a | 1 | 0 / 0 |
| W02 | claude-sonnet-5-5 | claude-sonnet-5-5 | 331,933 | 64 (74 tool_use blocks) | 1,011.0 s (16.8 min) | 1.2M / 250 / 90 min | 1 | 0 / 0 |
| W03 | claude-sonnet-5-5 | claude-sonnet-5-5 | 424,344 (202,149 + 222,195) | 43 (33 + 10) | 497.3 s (8.3 min) | 1.2M / 250 / 90 min | 1 + 1 correction round | 0 / 0 |
| W04 | claude-haiku-5-5 | claude-haiku-5-5 | 164,222 | 17 | 101.1 s (1.7 min; the child estimated about 15 min) | 400k / 80 / 30 min | 1 (no fallback) | 0 / 0 |
| **R2 total** | | | **920,498 of 3,000,000** | 124 | 1,609.4 s of child time (26.8 min) | 6 h wall | 4 dispatches of 5 (3 + the W03 resume) | 0 |

- "Observed" is the model named in each child's API responses: response-claimed, not provider-attested; effort UNKNOWN for all; no runtime receipt exists.
- Wall time: the R2 authorization arrived on 2026-10-23 and this return is written 2026-10-24T03:14Z; the interval includes a session-limit pause and a supervisor-session restart, so wall time is not a useful measure against the 6 h cap. Child work time was 26.8 min. No cap was hit.
- Team-lead correction rounds used: 1 of 2 (W03 status-line defect). Team-lead edit: one two-line change to the Verification section of `docs/02-how-to/memory-bridge.md` after W04 returned (it said plugin validate/test had not run; they had), committed in `52855fb35`.
- Intermediate model audits: 0. Advisor calls by children: 0 (structurally checked in every transcript). Coordinator advisor calls during execution: 0.

## Gate table (run by the coordinator at `52855fb35`)

| Gate | Result |
|---|---|
| `claude plugin validate plugins/dopemux-memory-bridge` | PASS, exit 0 (advisory warnings only: no icon, no marketplace install line; output in `PLUGIN_VALIDATE_OUTPUT.txt`) |
| `claude plugin test plugins/dopemux-memory-bridge` | PASS, 105 pass / 0 fail |
| `tsc -p` (strict, noUncheckedIndexedAccess, 2.1.304 declaration, register.tsx + register.test.ts) | PASS, exit 0 |
| `git diff --check origin/main..HEAD` | PASS |
| `validate_change_contract.py --base origin/main --head HEAD` | PASS (max_lane L2, 25 paths, model_audit_required) |
| Commit diffs vs allowlists (e561166a6, 1ce149a76, 52855fb35) | PASS: every commit inside its workstream allowlist |
| Docs: `docs_frontmatter_guard.py`, `docs_prohibited_patterns.sh`, `docs_validator.py` on the new file | PASS ×3 |
| Secret-shape grep over the plugin and docs (non-test) | PASS, no hits |
| Forbidden API grep (http.fetch, $.model, $.agent, session.append, advisor) in register.tsx | PASS: none in code (comments only) |
| `.venv/bin/pre-commit` and the other docs pre-commit hooks (prelude tokens, markdown location) | NOT_RUN: no `.venv` and no `pre-commit` in this worktree |
| `ct validate-macro` / `ct validate-binding` (R2 macro, coordinator and three child bindings) | PASS |
| Live session with the mod; real `dopemux capture emit`; any service | NOT_RUN by design |
| Final independent L2 audit | NOT_RUN: operator-gated |
| DCP route, Task Orchestrator state | NOT_RUN (unreachable) |

## What was and was not built

Built: per-session JSONL ring outbox with torn-write recovery; capture of goal, files, marker-detected decisions, TodoWrite completions; `📮` status line counting only replayable rows; welcome-back band that wraps `next(e)`; serial, bounded, idempotent replay of task and note rows to `dopemux capture emit` with a dead-row rule; `/bridge-note`; the how-to.
NOT_BUILT (W01 verdicts): session-start recap, `decision.logged`, dope-memory REST replay, any ConPort access.

## Remaining uncertainty

1. Live behaviour of everything: no session ever loaded the mod. `$.process` on the desktop surface is UNKNOWN; if absent there, the git segment and the replay never run.
2. Plugin order of Pulse versus this mod: Pulse draws its AbovePrompt without `next(e)` and can hide the band.
3. `$.fs.write` atomicity and the engine's acceptance of `idleMinutes` min/max are tested only against the test kit.
4. Replay writes raw ledger rows only; nothing local promotes them to the work log (only the Redis consumer does). The replay needs `services/working-memory-assistant` under the repo root and `dopemux` on PATH (the PATH copy is a non-editable install that can drift). About 2.8 s per call.
5. Pending task/note rows of an ended session are not replayed by another session (single-writer rule); a todo completed within about a minute of a session end stays pending.
6. The W03 token total may over-count; the model identity is response-claimed only.
7. Recap prerequisites remain open: `DMX-MEMSPINE-IDENTITY-005` (no implementing commit; a different write-only guard is on open PR #1446), P3 live check.

## Decisions left for the operator

1. **Final audit route** (the only remaining gate to a PR): `gemini-4-argon-high` should be available after about 2026-10-24T03:30Z (quota reset time as reported earlier; this return is written at 03:14Z and nothing was re-probed), or the Grok CLI tool-less recipe with explicit approval. Copy raw audit streams into this review bundle at once.
2. Whether to push and open a draft PR (not done; operator gates).
3. Recap: land `DMX-MEMSPINE-IDENTITY-005` (or an accepted equivalent covering reads) and a P3 live check, or rule that a ConPort-only recap from `/api/decisions` and `/api/recent-activity` with an explicit workspace is acceptable.
4. A live smoke test: load the mod in the desktop app in a checkout with `.dopemux/`, finish a turn, complete a todo, and run `/bridge-note hello`; check the status line, the outbox file and `sqlite3 .dopemux/chronicle.sqlite`.
5. Whether to add allowance fields to the macro schema (today they are enforced by the team lead only).
