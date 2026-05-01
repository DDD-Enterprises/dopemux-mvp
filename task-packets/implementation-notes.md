---
id: TP-DMX-FREEFLOW-ROUTER-0001-IMPLEMENTATION-NOTES
title: Strict-Free LLM Router Implementation Notes
type: explanation
owner: '@codex'
date: '2026-05-01'
author: '@hu3mann'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: Implementation notes for the strict-free LLM router task packet.
---
# Implementation Notes: Strict-Free LLM Router

Task packet: `task-packets/TP-DMX-FREEFLOW-ROUTER-0001.md`

## Changes

* Added `dopemux.freeflow` with a strict-free provider catalog, SQLite quota ledger, route decision recorder, hosted/local route scoring, quota checks, header-based cooldown ingestion, and strict-free LiteLLM config generation.
* Extended routing validation to support local providers with `auth_mode: none` or `auth_mode: ignored`.
* Added `dopemux routing freeflow doctor|quota|routes` commands with JSON output.
* Added freeflow provider/model/template defaults and LiteLLM callback admission control for route decision IDs, quota buckets, sensitivity, quota checks, usage events, and provider cooldown ingestion.
* Added focused tests for quota behavior, provider catalog coverage, privacy routing, strict-free config filtering, validation, trace metadata, and CLI JSON output.

## Verification

* `uv run --extra test python -m pytest tests/test_freeflow_router.py tests/test_freeflow_quota.py tests/test_freeflow_trace_logger.py` -> 18 passed.
* `uv run --extra test python -m pytest tests/test_litellm_proxy.py tests/test_litellm_manager.py services/repo-truth-extractor/tests/test_prescan_provider_catalog.py` -> 56 passed.
* `uv run --extra test python -m dopemux.cli routing freeflow doctor --offline --json` -> exit 0.
* `uv run --extra test python -m compileall -q src/dopemux/freeflow.py src/dopemux/routing_config.py src/dopemux/routing_cli.py src/dopemux/litellm_trace_logger.py` -> exit 0.
* `uv run --with pre-commit pre-commit run --files src/dopemux/freeflow.py src/dopemux/litellm_trace_logger.py src/dopemux/routing_cli.py src/dopemux/routing_config.py templates/routing.yaml tests/test_freeflow_quota.py tests/test_freeflow_router.py tests/test_freeflow_trace_logger.py task-packets/TP-DMX-FREEFLOW-ROUTER-0001.md task-packets/implementation-notes.md` -> exit 0.
* `git diff --check` -> exit 0.

## Residual Risk

* Live provider probes are intentionally not implemented in this slice.
* Workspace-specific quota limits for Mistral, GitHub Models, and Hugging Face credits remain advisory until runtime credentials can query account state.
* The current user-level `~/.dopemux/routing.yaml` loaded by the CLI did not have `freeflow.enabled: true`; the template and generated config path include strict-free policy, but existing installed user configs may need regeneration or manual migration.
