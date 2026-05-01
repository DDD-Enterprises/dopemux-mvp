---
id: TP-DMX-FREEFLOW-ROUTER-0001
title: Strict-Free LLM Router
type: explanation
owner: '@codex'
date: '2026-05-01'
author: '@hu3mann'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Strict-Free LLM Router (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DMX-FREEFLOW-ROUTER-0001 · Dopemux Routing · Strict-Free LLM Router

## Objective

Implement a strict-free, quota-aware routing layer around existing Dopemux LiteLLM routing surfaces.

## Scope

IN:

* Add strict-free provider catalog, quota ledger, and route selection logic.
* Add freeflow CLI inspection commands.
* Filter generated LiteLLM configs so strict-free mode excludes paid providers and paid fallbacks.
* Add targeted unit and CLI tests.

OUT:

* Live provider probes.
* Account/key/IP rotation or quota circumvention.
* Paid fallback enablement.

## Invariants

* Sensitive memory/context payloads may route only to local providers.
* Strict-free generated config must not include paid OpenAI, Anthropic, xAI, DeepSeek, Together, Fireworks, or paid OpenRouter routes.
* Quota and route decisions must be auditable without logging prompt or completion content.

## Plan

1. Add a freeflow policy module with provider catalog, quota ledger, route decisions, and LiteLLM config generation.
1. Extend routing config validation for local auth modes and strict-free policy validation.
1. Add `dopemux routing freeflow` doctor, quota, and routes commands.
1. Add tests for quota, route selection, strict-free filtering, local auth validation, and CLI JSON output.

## Files to Touch

* `src/dopemux/freeflow.py`
* `src/dopemux/routing_config.py`
* `src/dopemux/routing_cli.py`
* `src/dopemux/litellm_trace_logger.py`
* `templates/routing.yaml`
* `tests/test_freeflow_quota.py`
* `tests/test_freeflow_router.py`
* `tests/test_freeflow_trace_logger.py`
* `task-packets/implementation-notes.md`

## Exact Commands to Run

* `python -m pytest tests/test_litellm_proxy.py tests/test_litellm_manager.py services/repo-truth-extractor/tests/test_prescan_provider_catalog.py`
* `python -m pytest tests/test_freeflow_router.py tests/test_freeflow_quota.py`
* `python -m dopemux.cli routing freeflow doctor --offline --json`
* `git diff --check`

## Acceptance Criteria

* Strict-free route selection blocks paid providers.
* Sensitive route selection uses only local routes.
* Hosted free route selection respects configured credentials and quota counters.
* CLI JSON commands emit machine-readable policy/quota state.
* Targeted regression tests pass or blockers are reported with evidence.
