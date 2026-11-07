# MACRO-DMX-FOUNDATIONS-001 — Issuance Record (Foundations Wave 1)

**Issued**: 2026-10-30 by the Control Tower supervisor side session (Claude Code, team lead `claude-opus-5-5`; observed effort of the lead is UNKNOWN to the issuer, requested `high`).
**Authority**: NONE. Nothing in this package was executed, committed, pushed, signed or merged. This is issuance only. The package is untracked on purpose.

## Operator references (verbatim, chat 2026-10-30)

| Quote | What it covers |
|---|---|
| "Foundations first" | theme |
| "Looks right, write design" | scope playback |
| "Approve" | design `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md` |
| "Subagent-driven" | execution method for `docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md` |

**No literal AUTHORIZE line was given.** The template macro required `AUTHORIZE_..._EXECUTION=YES`; this one records the four quotes above as given and invents no token. Before W01 starts, the operator confirms in chat that these quotes are the execution authorization, or sends a literal line of their choosing. Until then `MACRO_PACKET.json` global_stop_conditions holds execution.

## Pins

| Item | Value |
|---|---|
| origin/main | `93050d135ffc2592000c1d0edef82b2912935525` |
| Branch | `feat/foundations-wave-1` in `/Users/hue/code/dopemux-mvp/.worktrees/foundations-wave-1` |
| HEAD at issuance | design + plan commits on top of that main (sha pinned in the MacroPacket objective) |
| Plan / design | `docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md`, `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md` |

If main has moved or the branch no longer descends from the issuance HEAD at start, the macro stops at its first precondition (NEEDS_SUPERVISOR) and is re-pinned, not adapted.

## Workstreams and TP_ROUTE

Workstreams map 1:1 to plan Tasks 1-5 and run **serially** (`max_mutating_workstreams` 1), one mutating implementer each. Plan Task 6 (freeze checks, join J06) belongs to the team lead.

| WS | Plan task | Write surface | Deps | Implementer |
|---|---|---|---|---|
| W01 | 1 CI step | `.github/workflows/ci-complete.yml` | — | claude-haiku-5-5 |
| W02 | 2 engine methods + parity test | `services/adhd_engine/core/engine.py`, `tests/arch/test_adhd_engine_mcp_parity.py` | — | claude-sonnet-5-5 |
| W03 | 3 `dopemux adhd status` | `src/dopemux/commands/adhd_commands.py`, `src/dopemux/cli.py`, `tests/unit/test_adhd_commands.py` | — | claude-sonnet-5-5 |
| W04 | 4 port drift test | `tests/arch/test_service_port_drift.py`, `src/dopemux/config/manager.py` | W03 | claude-sonnet-5-5 |
| W05 | 5 docs | `docs/03-reference/adhd-status-cli.md`, `docs/03-reference/ci-contract-gates.md`, `docs/00-MASTER-INDEX.md`, `docs/docs_index.yaml`, `.claude/claude.md`, `AGENTS.md` | W01-W04 | claude-sonnet-5-5 |

Forbidden for every workstream: `services/adhd_engine/api/routes.py`, `services/adhd_engine/tests/test_state_contract.py`, `.mcp.json`, `mcp_catalog.yaml`, `.claude/statusline.sh`, `scripts/dopemux_dashboard.py`, anything under `plugins/`.

```
TP_ROUTE   (team lead)
runner=claude-code-desktop  model=claude-opus-5-5  effort=high
why=The supervising session coordinates, runs the freeze checks and the advisory whole-branch review; implementers are pinned cheaper.
```

```
TP_ROUTE   (W01)   runner=claude-code  model=claude-haiku-5-5   effort=low
why=One YAML step plus one validation run. Escalate to Sonnet only if the CI-equivalent run fails.
TP_ROUTE   (W02-W05) runner=claude-code  model=claude-sonnet-5-5 effort=medium
why=Engine code, new CLI, test design, docs: moderate judgment; escalation one tier up for fix rounds 4-5 only.
TP_ROUTE   (per-task reviewer) runner=claude-code model=claude-sonnet-5-5 effort=medium
TP_ROUTE   (final whole-branch review) runner=claude-code model=claude-opus-5-5 effort=high — ADVISORY, not the audit.
```

Effort values for children are the issuer's lowest-sufficient selection; requested identity is not proof of execution identity (observed identity UNKNOWN without runtime receipts).

## Joins

Each workstream's named tests/commands must pass before the next starts (J01-J05). J06 is the team-lead freeze: CI-equivalent `tests/arch` on Python 3.11, `pytest tests/unit` with no new failures against origin/main, `validate_change_contract.py` status=PASS max_lane=L2. Then STOP.

## Audit (PROPOSED ONLY)

`AUDITOR_BINDING_PROPOSED.json`: `grok-cli` / `grok-4.5`, tool-less sealed prompt, one attempt, zero retries, no fallback, same contained recipe as the PULSE packages. **The operator has not authorized this route**, and it is not selected, recorded or run. Exactly one final independent audit, after freeze. Timing (design section 5): after PRs #1482, #1472 and #1483 merge, unless the operator decides otherwise; each later merge before then would cost one re-audit. No intermediate model audits.

## Rollback and delivery

Per workstream: `git revert` of that workstream's commit(s) on `feat/foundations-wave-1`. Workstreams push nothing. Push (a workflow-file push may need the `workflow` token scope; if refused the operator pushes) and the draft PR are operator-approved team-lead steps after freeze.

## Known disagreement to note

Design section 7 says W1-W4 "can run in parallel (disjoint files)". This issuance serializes them as instructed; the plan itself makes W04 depend on W03.

## AMENDMENT-01 (supervisor, 2026-10-30)

The execution hold in `authority.global_stop_conditions[0]` is released. The operator answered "Subagent-driven" to the question "which execution approach should the plan use?", after approving the design ("Approve"). The supervisor rules that reply is the execution authorization for this macro. It covers local commits on `feat/foundations-wave-1` only: no push, PR, merge or audit, and the audit route stays PROPOSED and operator-gated (`global_stop_conditions[6]`). If the operator wanted a literal token, nothing has left the worktree and execution stops on their word.

## AMENDMENT-02 (supervisor, 2026-10-30)

`scripts/governance/validate_change_contract.py --base origin/main --head HEAD` reports `max_lane=L3`: `.github/workflows/ci-complete.yml` (W01) is classified L3; every other path in the wave is L2. W01's `delivery_risk_lane` (macro) and `risk_lane` (task packet) are raised to L3 and the macro's W01 sha256 ref is recomputed. The one final audit must be eligible for an L3 subject; the operator's audit-route decision has to take that into account. No other field changes.

## AMENDMENT-03 (supervisor, 2026-10-30)

The final whole-branch review (advisory, claude-opus-5-5, not the audit) returned "With fixes": one Important (CI runs Python 3.12.13 via `.python-version`, not 3.11) and nine Minors. One fix wave (claude-sonnet-5-5) addresses the Important plus Minors 1-6, 8, 9 and the timeout assertion, with a write set equal to the files named in the fix list: `docs/03-reference/ci-contract-gates.md`, `docs/03-reference/adhd-status-cli.md`, `docs/91-rfc/rfc-2026-10-30-foundations-wave-1.md`, `docs/91-rfc/rfc-2026-10-30-foundations-wave-1-plan.md` (erratum line only), `src/dopemux/commands/adhd_commands.py`, `tests/unit/test_adhd_commands.py`, `services/adhd_engine/core/engine.py`, `tests/arch/test_adhd_engine_mcp_parity.py`, `tests/arch/test_service_port_drift.py`, `.github/workflows/ci-complete.yml`. Statements in this package that CI runs Python 3.11 should be read as 3.12.13.
