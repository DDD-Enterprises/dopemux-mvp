---
id: TP-RTE-TRUTH-LOAD-PLAN
title: RTE-TRUTH Load Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-15'
last_review: '2026-07-15'
next_review: '2026-10-13'
prelude: Execution order, dependencies, and model routing for the 32 TP-RTE-TRUTH
  remediation packets produced by the Repo Truth Extractor audit.
---
# TP-RTE-TRUTH Load Plan — RTE audit remediation (Grok build)

**Program**: RTE-TRUTH (audit complete 2026-07-11; findings: `claudedocs/rte-truth-program-2026-07/CONSOLIDATED-FINDINGS.md`)
**Base branch**: `claude/rte-audit-improvement-f4beb7` (contains P0 truth harness `85371b4df`, R0-001 `605872591`, R0-002 `734a0e690`, R0-005 partial `e7fbd4a32`, audit reports `18d08e228`)
**Executor**: Grok (`grok-code-fast-1`) per operator directive; opus-class review at PAL codereview steps; orchestrator tree root `7212c3b8` (tags `rte-truth`)
**Global rules**: dry-run only (no `--execute`, no `DPMX_LIVE_OK`); golden harness (`tests/test_truth_harness_goldens.py`) is the behavior contract; seam PRs may NOT update goldens; R2/R4 packets that intentionally change goldens must itemize the diff in PROOF.json.

## Recommended model routing

The existing `execution.agent` / `execution.model` fields remain the original executor intent. The new `execution.recommended_model` and `execution.recommended_reasoning_effort` fields are the current Codex routing recommendation.

| Packet | Recommended model | Reasoning |
|---|---|---|
| R0-001 | `gpt-5.6-luna` | `medium` |
| R0-002 | `gpt-5.6-luna` | `medium` |
| R0-003 | `gpt-5.6-luna` | `medium` |
| R0-004 | `gpt-5.6-luna` | `high` |
| R0-005 | `gpt-5.6-terra` | `high` |
| R0-006 | `gpt-5.6-terra` | `high` |
| R0-007 | `gpt-5.6-luna` | `high` |
| R0-008 | `gpt-5.6-sol` | `max` |
| R1-001 | `gpt-5.6-terra` | `xhigh` |
| R1-002 | `gpt-5.6-terra` | `xhigh` |
| R1-003 | `gpt-5.6-terra` | `xhigh` |
| R1-004 | `gpt-5.6-sol` | `max` |
| R2-001 | `gpt-5.6-sol` | `max` |
| R2-002 | `gpt-5.6-terra` | `xhigh` |
| R2-003 | `gpt-5.6-sol` | `max` |
| R2-004 | `gpt-5.6-sol` | `max` |
| R2-005 | `gpt-5.6-sol` | `max` |
| R3-001 | `gpt-5.6-sol` | `xhigh` |
| R3-002 | `gpt-5.6-sol` | `max` |
| R3-003 | `gpt-5.6-sol` | `max` |
| R3-004 | `gpt-5.6-sol` | `max` |
| R3-005a | `gpt-5.6-terra` | `high` |
| R3-005b | `gpt-5.6-sol` | `xhigh` |
| R3-005c | `gpt-5.6-sol` | `xhigh` |
| R3-005d | `gpt-5.6-sol` | `xhigh` |
| R3-005e | `gpt-5.6-terra` | `high` |
| R3-006 | `gpt-5.6-sol` | `xhigh` |
| R4-001 | `gpt-5.6-terra` | `xhigh` |
| R4-002 | `gpt-5.6-terra` | `xhigh` |
| R4-003 | `gpt-5.6-terra` | `xhigh` |
| R4-004 | `gpt-5.6-terra` | `xhigh` |
| R4-005 | `gpt-5.6-luna` | `medium` |
| R4-006 | `gpt-5.6-terra` | `xhigh` |
| R5-001 | `gpt-5.6-sol` | `max` |

Every handoff must display the selected packet and both routing tags in its requested-next-step line:

`Requested Next Step: <packet> | recommended model: <model> | reasoning: <effort>`

## Status at load
| Packet | Status |
|---|---|
| R0-001, R0-002 | **DONE** (commits above) |
| R0-005 | partial WIP staged at `e7fbd4a32` — executor finishes |
| R0-008 | **BLOCKED** — operator fixtures decision (which committed extraction/ runs are load-bearing) |
| all others | ready per dependency order below |

## Execution order (within-wave deps; waves gate via orchestrator)
- **R0** (parallel-safe): 003, 004, 005, 006, 007 · 008 blocked
- **R1** (STRICTLY SEQUENTIAL, exclusive v5 ownership): 001 → 002 → 003 → 004
- **R2** (after R1-004): 001 → 002, 001 → 003 · 004 (after R1-004) · 005 (after R0-005)
- **R3**: 001 first (gates schema work) → 003, 004, 005a–e · 004 → 006 · 002 after R1-004
- **R4**: 001 anytime · 002 after R1-002 → 003, 004, 006 · 005 after 001+002
- **R5**: 001 last (after R4-003 + R4-005). **v3 deletion EXCLUDED** (deferred post-release).

## Priority guidance (if serializing)
1. R4-001 (wizard statically broken — CRIT, no deps)
2. R3-001 (C9 — gates all prompt schema value)
3. R1-001..004 (unblocks R2/R3-002/R4-002 chains)
4. R2-001 (pricing truth CRIT)
5. R3-002 (injection separator CRIT)

## Requested next step

`TP-RTE-TRUTH-R1-002 | recommended model: gpt-5.6-terra | reasoning: xhigh`
