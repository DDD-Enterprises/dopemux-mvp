# MACRO-DMX-MEMORY-BRIDGE-001-R2 — Issuance Record (amends R1 after W01)

**Issued**: 2026-10-23 (coordinator binding recorded 20:38:50Z) by the Control Tower supervisor side session (Claude Code desktop, `claude-sonnet-5-5`, effort `high`).
**Why**: the commissioning session asked to pause after the read-only W01 and add numeric allowances before any implementation runs. W01 also changed the scope, so R1's W02-W05 could not run as written.
**R1 is preserved unchanged** (`task-packets/MACRO-DMX-MEMORY-BRIDGE-001/`, hashes in its `ISSUANCE.md`; `shasum -c` on its flattened copy passes). Its authorization covers R1 only.
**Base**: `93050d135ffc2592000c1d0edef82b2912935525` (= origin/main = HEAD). Authority: NONE.

## Execution gate

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_R2_EXECUTION=YES
```

The earlier verbatim authorization does not cover R2. Nothing in R2 has run.

## Package members (the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `560dbae3ffcd23b91b28875d3051ad391d13bc344935f275bc34804b2ef29145` |
| `EXECUTION_BINDING.json` (coordinator) | `8340e49ad491d559421dded0e3d849ff4873f7202d0cf1e3427dae798491c1e7` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `86b499a54a7817a0d28511197c6d783e1c1833d40004dbe199a7aa07096c4d61` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `c108e09b25b035230639ca351d440387b872c917204599284e601b1f3de47c8c` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `be814deba35cbf90a78a34a39f28647b13e824a9f78243ff5ff42eae6de5b273` |

Evidence input pinned in every child (C09): `proof/MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/W01_FINDINGS.md`, sha256 `ccc05d92571130d0aed95adc1216214585ebaf4eee6f65c2c42f2e18cd9c70bd` (205 lines, untracked until committed).

## W01 verdicts (read-only, done)

| Sub-feature | Verdict | Decisive evidence |
|---|---|---|
| outbox | GO_REDUCED | no append/rename/delete in `$.fs`, no plugin data dir: per-session ring file under gitignored `.dopemux/` (.gitignore:140, :299) |
| status_count | GO | `ui.status` is one line per plugin; coexists with Pulse |
| band | GO_REDUCED | Pulse's AbovePrompt hook (register.tsx:343-353) draws without `next(e)` and can hide ours; ours must wrap `next(e)`; terminal and desktop only |
| replay → local ledger (`dopemux capture emit`) | GO_REDUCED | idempotent by stable event_id; CLI-only, raw rows only, needs the service tree under the repo root, about 2.8 s per call |
| replay → dope-memory REST | **NO_GO** | `memory_store` not idempotent (uuid4 source id), no auth, no summary redaction |
| recap | **NO_GO** | identity not fail-closed on base; `DMX-MEMSPINE-IDENTITY-005` has no implementing commit (a different write-only guard sits on open PR #1446); P3 mismatch proven in source; ConPort `GET /api/context` inserts a row (enhanced_server.py:541-571) |
| `decision.logged` | NOT_BUILT | ConPort already emits it; doctrine "Decisions: log in ConPort only" |
| `task.completed` / `manual.memory_store` | buildable | TodoWrite transitions / a mod slash command |

All live probes (3020, 3004, 3025, 3005) were refused: **NOT_RUN**. `dopemux` on PATH resolves and `capture emit --help` exits 0; its capture files are byte-identical to the worktree's. The W01 return also disclosed one read-only `gh pr list` (GitHub metadata, outside the packet's literal network list) and that the R1 verify command `git diff --name-only` cannot see an untracked new file (R2 verify adds `git status --porcelain`).

## What changed from R1

| R1 | R2 |
|---|---|
| W01 read-only investigation | done; pinned as evidence, not re-run |
| W02 outbox + band (single file, append) | W02 with W01's ring-per-session design, TodoWrite capture, band that wraps `next(e)` |
| W03 replay to dope-memory and ledger | W03 **ledger only**, serial and bounded, dead-row path, plus a `bridge-note` command |
| W04 recap (conditional) | **removed**: NOT_BUILT with W01's blockers |
| W05 docs | W04 docs, with a mandatory "Not built" section |
| gate-table dispatch | none needed: W01's result is fixed input |
| no numeric limits | PROPOSED allowances below |

## PROPOSED allowances (marked PROPOSED; accepted only by authorizing R2)

| Scope | Elapsed | Subagent tokens | Tool uses | Attempts | Review rounds |
|---|---|---|---|---|---|
| W02 | 90 min | 1,200,000 | 250 | 1 + 1 retry | 1 re-read + ≤1 correction |
| W03 | 90 min | 1,200,000 | 250 | 1 + 1 retry | 1 re-read + ≤1 correction |
| W04 (docs) | 30 min | 400,000 | 80 | 1 Haiku + 1 Sonnet fallback (the fallback is the retry) | 1 re-read + ≤1 correction |
| **Macro** | 6 h to a frozen head | 3,000,000 total | — | 5 dispatches total (3 + at most 2 retries/fallbacks) | 2 correction rounds total |

- **Model calls**: intermediate audits 0; `advisor` 0 for every child and the coordinator; final independent audit 1, outside this budget, on an operator-approved route.
- **Active time** (model-working time) is **not recordable** by the harness: UNKNOWN. Elapsed wall time is the enforceable bound.
- **Basis (judgment, no price evidence; cost UNKNOWN)**: W01, a 12-question read-only investigation, used 335,949 subagent tokens, 123 tool uses and 815.8 s wall (completion notice). Builds are TDD with test and validation runs, so I scaled tokens about 3.5× and wall time about 6.6× for the two builds, and about 1/3 of that for docs. They are caps, not forecasts.
- **Recordable counters**: `duration_ms`, `subagent_tokens`, `tool_uses` from each completion notice. Coordinator tokens are visible to the session but not capped.
- **Stop conditions on a cap** (A03): stop the workstream, start no further attempt, preserve the uncommitted diff, return NEEDS_SUPERVISOR with counters and evidence. No model upgrade, provider change or extra attempt without a new operator ruling. Macro cap hit: stop dispatching, return a partial aggregate.
- **Enforcement gap**: `macro_packet.v2` has `additionalProperties: false` and no allowance fields, so the numbers live in each child's invariants (A01-A03), the macro `base_policy`, `global_stop_conditions` and `final_audit_policy` text. `ct validate-macro` does not check them; the team lead does. A schema field would be a separate contract change.

## TP_ROUTE

```
TP_ROUTE   (W02, W03)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=plugin-authoring, task-packet
why=hook code with file and subprocess I/O and privacy handling; the model that completed W01 within budget; cost UNKNOWN

TP_ROUTE   (W04)
runner=claude-code-agent
model=claude-haiku-5-5   (fallback claude-sonnet-5-5 on an evidence-backed STOP only)
effort=UNKNOWN
skills=NONE
why=docs derived from committed files; cheapest adequate
```

W01 requested vs observed: requested `claude-sonnet-5-5`; observed UNKNOWN (no runtime receipt); effort UNKNOWN; advisor calls reported 0 by the child (not structurally verified from its transcript).

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro` (R2) | PASS, STATIC_VALID |
| `ct bind-record` + `ct validate-binding` (R2 coordinator) | PASS |
| `task_packet.v2` schema W02-W04 | PASS ×3 |
| Macro pins (3 task packets + binding) | MATCH |
| R1 flattened proof `shasum -c` | PASS (no R1 file changed) |
| Child bindings for R2 | NOT_RUN: created per child at dispatch |
| Live behaviour of any service | NOT_RUN |

## State of the checkout (nothing committed)

`git status`: untracked `task-packets/MACRO-DMX-MEMORY-BRIDGE-001/`, `task-packets/MACRO-DMX-MEMORY-BRIDGE-001-R2/` and `proof/MACRO-DMX-MEMORY-BRIDGE-001/` (the flattened R1 package, `AUTHORIZATION_RECORD.md` and `W01_FINDINGS.md`). My attempt to commit the flattened R1 proof was denied by the auto-mode classifier, so it stays untracked; this is not worked around. Before W02 starts, the team lead commits the evidence (flat `review_bundle/` files only, explicit pathspec). The `task-packets/` folders must not be committed (preflight rejects GEC v2 packets there).

## Decisions for the operator

1. **Authorize R2** with the line above (or amend the allowances first).
2. **Recap**: stays NOT_BUILT. Unblock by landing `DMX-MEMSPINE-IDENTITY-005` (or an accepted equivalent covering reads) and a P3 live check, or rule that a ConPort-only recap from `/api/decisions` and `/api/recent-activity` with an explicit `workspace_id` is acceptable (W01 says only that variant is unblocked, and it needs your ruling).
3. **Final audit route**: unchanged and still yours: `gemini-4-argon-high` after about 2026-10-24T03:30Z, or the Grok CLI tool-less recipe.
4. **Desktop surface**: `$.process` behaviour on claude-desktop is UNKNOWN; if it is absent there, the git segment and the ledger replay never run for you. One runtime test of the loaded mod settles it.
