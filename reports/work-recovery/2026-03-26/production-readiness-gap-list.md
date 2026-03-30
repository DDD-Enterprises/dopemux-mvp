---
title: repo-truth-extractor production readiness gap list
doc_type: audit-report
status: active
created: '2026-03-26'
updated: '2026-03-26'
owner: codex
summary: Remaining direct reimplementation work after the first selective salvage pass in the extractor recovery worktree.
---

# Remaining Production-Readiness Gaps

The following items remain pending after the first selective salvage pass. They were not imported from the archived staged patch because their runtime authority, contract impact, or provider-model truth still needs direct reimplementation and validation.

## Runtime and policy gaps
- provider-safe live batch retrieval unification across OpenAI, Gemini, and xAI
- explicit OpenRouter live-batch rejection across all public batch entrypoints
- phase-scoped live-batch enforcement and multi-phase override gating
- dual live-consent guard for all live batch operations (`--execute` plus `DPMX_LIVE_OK=1`)
- spend ledger and cap enforcement
- generic circuit-breaker integration for batch paths
- staged `validate-live` ramp (`provider_probe`, `batch_pilot`, `phase_slice`, `full_phased`)
- branded validation UX layer

## Routing and model truth gaps
- verified provider-model audit against current official docs / PAL evidence
- direct reimplementation of any routing ladder refresh needed in `run_extraction_v5.py`
- direct reimplementation of any JSON-managed route refresh needed in `promptsets/v4/model_map.yaml`
- revalidation of preflight / provider-preflight semantics after routing updates

## Test and contract gaps
- pre-live gate implementation and its missing module surface
- TP-008 drift contract updates
- phase D contract-lane and promptpack route expectations
- v3 routing and escalation test updates
- parser-contract review for JSON salvage behavior changes

## Operator and docs gaps
- authoritative batch quickstart and operator workflow updates
- authoritative docs for staged validation, spend caps, and provider support matrix
- draft PR / commit workflow once direct implementation work is complete and validated
