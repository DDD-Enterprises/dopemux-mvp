---
id: rte-04-fl-routing-and-benchmark-governance-evidence
title: Rte 04 Fl Routing And Benchmark Governance Evidence
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Rte 04 Fl Routing And Benchmark Governance Evidence (reference) for dopemux
  documentation and developer workflows.
---
# RTE-04 FL Routing and Benchmark Governance Evidence

## Packet boundary

- Worktree/clone: `/tmp/dopemux-rte-04-fl-routing-and-benchmark-governance`
- Branch: `packet/rte-04-fl-routing-and-benchmark-governance`
- Base commit: `11a0da156`

## Ladder truth matrix

| provider | model slug | current code location | classification | authority source | proposed action |
| --- | --- | --- | --- | --- | --- |
| `gemini` | `gemini-3-flash-preview` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only until confirmed by a canonical registry refresh |
| `gemini` | `gemini-3.1-pro-preview` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only until confirmed by a canonical registry refresh |
| `openrouter` | `openai/gpt-5.3-codex` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only; do not treat as canonical production truth |
| `openrouter` | `openai/gpt-5.2` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only; replace only after operator confirmation if production use is desired |
| `openrouter` | `anthropic/claude-opus-4-6` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only; normalized handoff pack currently confirms `anthropic/claude-sonnet-4` instead |
| `xai` | `grok-4-1-fast-reasoning` | `services/repo-truth-extractor/fl_int/models.py` | `future_target` | `docs/05-audit-reports/rte-state-of-work-audit-20260410.md` | Keep benchmark-only until a canonical registry source confirms the slug |

Observed result from current repo truth:

- No current FL_INT ladder slug is confirmed by `audit_prep/prompt1_handoff_pack_normalized.md`.
- No current FL_INT ladder slug was reclassified as `stale` in this packet because the audit source frames them as forward-looking or unresolved, not disproven or removed.

## BM-LIVE posture

Current benchmark live posture is `partial`, not `not_started`.

Evidence:

- `services/repo-truth-extractor/benchmarking/executors/extraction_v5_adapter.py` supports `live_execution`, appends `--execute`, and requires `DPMX_LIVE_OK=1`.
- `services/repo-truth-extractor/benchmarking/executors/fl_int_adapter.py` remains fixture-backed and always runs `--dry-run`.
- `services/repo-truth-extractor/tests/test_benchmark_live_route_readiness_smoke.py` exercises provider-readiness aggregation, which shows benchmark live-readiness gates exist but does not prove end-to-end live campaigns have been executed.

Operational posture from those facts:

- `runtime_v5_extraction` is live-capable behind explicit operator consent.
- `fl_int`, `prescan`, and `phase_s` benchmark adapters remain non-live or fixture-backed in current repo truth.
- Broader benchmark campaigns should still be treated as staged, not production-enabled.

## Governance decisions recorded or still pending

Recorded by current repo truth as still requiring operator authority:

- promotion thresholds for benchmark-driven routing changes
- benchmark budget caps before broader BM-LIVE execution
- phase S policy-gating posture
- local or open-weight graduation criteria
- OpenClaw write authority over benchmark artifacts

Packet outcome:

- ladder status is now explicit in code, not silent
- BM-LIVE posture is documented from current partial state
- unresolved governance items remain explicitly pending rather than implied complete
