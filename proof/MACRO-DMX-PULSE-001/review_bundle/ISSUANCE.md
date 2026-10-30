# MACRO-DMX-PULSE-001 — Issuance Record

**Issued**: 2026-10-21T20:04Z by the Control Tower supervisor session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`, observed via `get_session`).
**Operator instruction**: "1,2,3" (next-work list, item 3 = Pulse), and the answer "In the repo (Recommended)" for where Pulse lives.
**Source**: `claudedocs/dopemux-mods-plugins-opportunity-map-2026-10-16.md` §3, §4.1 (M1, M2) and §6 (P1).
**Base**: `origin/main` = `95e95bee88cae5e6c95e6e34f7c28bb423ad9496` (fetched 2026-10-21).
**Authority**: NONE. This record and the package grant no execution authority.

## Execution gate

Implementation starts only after the operator types, in chat:

```
AUTHORIZE_MACRO_DMX_PULSE_001_EXECUTION=YES
```

## Package members (immutable; the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `d316a20b5aaed9781e630c93fa4f616bc2f2e8f5bcef917d3890493156ad0a51` |
| `EXECUTION_BINDING.json` (coordinator) | `07a70d10658613e329d4c74d9851cd18b115d85e44f1dd3ba67978e36d1239db` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `2245af78962a9c82837b6264e180f46ba8703326505eab491a506639ad7d6d35` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `76ebafc930bcd1ced8de34f54987be215ace6bdaa99bba5becaa384012ce7e56` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `76199835cd7e46593a83076567515e8fecc14441dd78d0b06ebd90e59ac5bc5e` |

This file is not referenced by the macro and is not part of the pinned subject.

## Workstreams and TP_ROUTE

| WS | Objective | Write allowlist | Deps | Group | Route (preferred → fallback) |
|---|---|---|---|---|---|
| W01 | ADHD Engine `/api/v1/state` serves `energy_level`/`attention_state` alongside `energy`/`attention` (non-breaking), with a contract test. Fixes the TUI, `check_energy.sh`, tmux script and dope-memory recap, which silently show defaults today. | `services/adhd_engine/api/routes.py` (the `/state` handler only), `services/adhd_engine/tests/test_state_contract.py` (new) | — | P1 | claude-sonnet-5-5 |
| W02 | The read-only `dopemux-pulse` mod: M1 status line (energy, attention, own session minutes, engine-down toast) and M2 focus clock (`/focus`, `/break`, `/done`, band above the prompt, limit toast, 90-minute nudge) | `plugins/dopemux-pulse/**`: `plugin.json`, `hooks/hooks.json`, `hooks/register.tsx`, `hooks/register.test.ts`, `README.md` (`types/index.d.ts` only by supervisor ruling) | — | P1 | claude-sonnet-5-5 |
| W03 | How-to documentation derived from the committed W02 files | `docs/02-how-to/pulse-status-line.md` | W02 | P2 | claude-haiku-5-5 → claude-sonnet-5-5 (fallback only on an evidence-backed STOP) |

- **Runner**: every child runs as `claude-code-agent`. Effort is `UNKNOWN` (not settable per child from this runner).
- **Parallelism**: W01 and W02 are proven DISJOINT and may run together (`max_mutating_workstreams` = 2); W03 follows W02.
- **Lane**: L2 for all (`services/` and `plugins/` match no lower rule). Exactly one final independent audit, different family, operator-gated route.

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro --file MACRO_PACKET.json` | PASS — `STATIC_VALID`, 0 errors |
| `ct validate-binding --file EXECUTION_BINDING.json` | PASS |
| `task_packet.v2` schema W01–W03 | PASS ×3 |
| Pair classification | W01/W02 and W01/W03 DISJOINT; W02/W03 DEPENDENCY_SERIALIZED |
| DCP route / Task Orchestrator state | NOT_RUN (task-orchestrator unreachable) |

## Facts the design rests on (checked 2026-10-21)

- `/state` is mounted at `/api/v1` (`services/adhd_engine/main.py:531`). It returns `energy`, `attention`, `session_minutes`, `user_id`; `session_minutes` is always 0 because `_session_start_times` is never set.
- Consumers reading the old keys: `src/dopemux/ui/dashboard.py:146-147`, `.claude/hooks/check_energy.sh:21`, `services/adhd_engine/scripts/adhd-tmux-status.sh:24-25`, `services/working-memory-assistant/dope_memory_main.py:81-82`.
- The engine's host port is 3025 (`services/registry.yaml`). `plugins` is an allowed root directory (`config/repo_hygiene/root_hygiene_policy.json`), so no policy change is needed.
- No test covers `/state` today.

## Open items the operator should know before authorizing

1. **Declaration file.** W02 must read this build's `claude-code.d.ts`, which the `plugin-authoring` skill writes when loaded. The coordinator loads it and hands W02 the path at dispatch; the path is session-specific (the old one is already gone).
2. **No live proof.** Nothing in this macro runs a real session with the mod against a running engine: that is NOT_RUN by design and is the operator's step. The mod is read-only toward the engine.
3. **Audit route.** `agy` `gemini-3.1-pro-high` was unavailable on 2026-10-18; a fallback needs explicit operator approval when the audit runs.
4. **Placement lessons from the command repair (apply at execution).**
   - The issuance package must not live under `task-packets/` in the branch: the preflight rejects GEC v2 packets and frontmatter-less returns there. Keep it under `proof/MACRO-DMX-PULSE-001/review_bundle/` as flat `.txt/.json/.md` files.
   - `proof-only` closure allows only `PROOF.json`, `.sig`, `AUDITOR_REPORT.md` and flat `review_bundle/` files.
   - Do not commit while a sibling worker is still editing the same worktree.
5. **Out of scope** (separate packets): fixing `session_minutes` in `core/engine.py`, the Memory Bridge mod, the Route Ledger mod, updating the other `/state` consumers, a marketplace manifest (a top-level `.claude-plugin/` is not an allowed root directory).

## Execution outline (after the gate)

1. Fresh worktree `.worktrees/pulse-001` on `feat/pulse-001` from freshly fetched `origin/main`; HEAD hard-equal; clean porcelain. Copy this package in (flat, under `proof/…/review_bundle/`) and re-verify the SHA-256s.
2. `ct bind-record` + `ct validate-binding` per child before dispatch.
3. Dispatch W01 (Sonnet) and W02 (Sonnet, with the declaration path) in parallel. Children never commit, push, or call `advisor`. Coordinator re-reads each diff, parses transcripts, commits one workstream per commit with an explicit pathspec.
4. Dispatch W03 (Haiku) after the W02 commit.
5. Gates: tests, `claude plugin validate/test`, black/flake8, `validate_change_contract` plus the proof-only form, pre-commit range. Freeze (J02), then one final audit on the operator-approved route, then the proof bundle.
6. Aggregate return (authority NONE). Push, PR and merge remain operator gates.
