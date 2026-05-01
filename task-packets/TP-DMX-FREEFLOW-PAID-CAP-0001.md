---
id: TP-DMX-FREEFLOW-PAID-CAP-0001
title: Freeflow Paid-Cap Cheap Routing
type: explanation
owner: '@codex'
date: '2026-05-01'
author: '@hu3mann'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Opt-in paid-cap extension for Freeflow routing and cheap/self-host provider research.
---
# Task Packet: TP-DMX-FREEFLOW-PAID-CAP-0001 - Dopemux Routing - Paid-Cap Cheap Routing

## Objective

Extend the strict-free Freeflow router with an explicit, opt-in paid-cap layer for super-cheap hosted routes while preserving fail-closed strict-free defaults and local-only sensitive routing.

## Scope

IN:

* Add catalog metadata for low-cost paid-cap candidates.
* Add an append-only spend ledger and daily/monthly cap checks.
* Generate LiteLLM config entries for paid-cap routes only when `freeflow.paid_cap.enabled` is true and the model is allowlisted.
* Enforce paid caps in the LiteLLM pre-call hook before upstream calls.
* Use the Gemini Flash-Lite preview paid route as the first cheap fallback.
* Capture current self-hosted and cheap hosted research.
* Add focused unit and trace tests.

OUT:

* Enabling paid routing by default.
* Account, key, IP, or quota rotation.
* Live provider probes.
* Cloud GPU deployment automation.
* Replacing strict-free hosted quota behavior.

## Invariants

* Strict-free mode remains strict-free unless `freeflow.paid_cap.enabled` is explicitly true.
* Paid-cap routes must be allowlisted by model name.
* Sensitive memory/context payloads may never select hosted paid-cap routes.
* Spend decisions must be auditable without logging prompt or completion content.
* Hidden paid default fallbacks remain blocked when paid-cap is disabled.

## Plan

1. Add paid-cap provider catalog records and model pricing metadata.
2. Add `spend_events` and paid-cap checking to the Freeflow ledger.
3. Include paid-cap routes in generated LiteLLM config only when enabled and allowlisted.
4. Reserve estimated paid spend in the LiteLLM pre-call hook before calling upstream providers.
5. Add CLI/doctor visibility through existing Freeflow JSON surfaces.
6. Add focused tests for paid-cap filtering, cap math, privacy policy, and trace enforcement.
7. Add research notes covering local, cheap hosted, and self-host cloud options.

## Files to Touch

* `src/dopemux/freeflow.py`
* `src/dopemux/litellm_trace_logger.py`
* `src/dopemux/routing_cli.py`
* `templates/routing.yaml`
* `tests/test_freeflow_quota.py`
* `tests/test_freeflow_router.py`
* `tests/test_freeflow_trace_logger.py`
* `task-packets/TP-DMX-FREEFLOW-PAID-CAP-0001.md`
* `task-packets/freeflow-paid-cap-research.md`
* `task-packets/implementation-notes.md`

## Exact Commands to Run

* `uv run --extra test python -m pytest tests/test_freeflow_router.py tests/test_freeflow_quota.py tests/test_freeflow_trace_logger.py`
* `uv run --extra test python -m pytest tests/test_litellm_proxy.py tests/test_litellm_manager.py services/repo-truth-extractor/tests/test_prescan_provider_catalog.py`
* `uv run --extra test python -m dopemux.cli routing freeflow doctor --offline --json`
* `uv run --extra test python -m compileall -q src/dopemux/freeflow.py src/dopemux/routing_config.py src/dopemux/routing_cli.py src/dopemux/litellm_trace_logger.py`
* `git diff --check`

## Acceptance Criteria

* Paid-cap disabled config contains no paid-cap routes.
* Paid-cap enabled config contains only allowlisted paid-cap routes.
* The first Gemini paid-cap route uses `gemini/gemini-2.5-flash-lite-preview-09-2025`.
* Paid-cap spend reservations block requests that would exceed daily or monthly caps.
* Sensitive requests do not select paid-cap hosted routes.
* Doctor/quota JSON exposes paid-cap and spend state.
