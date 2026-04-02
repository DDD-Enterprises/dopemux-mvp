---
id: repo-truth-extractor-v5-offline-envelope
title: Repo Truth Extractor V5 Offline Envelope
type: runbook
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Repo Truth Extractor V5 Offline Envelope (runbook) for dopemux documentation
  and developer workflows.
---
# Repo Truth Extractor v5 Offline Envelope

## Current truth

- As of April 2, 2026, bounded online first-live readiness remains environment-blocked when the required OpenRouter models are not authorized in the current environment.
- This does not mean the v5 repo/tooling path is unusable.
- It means operators should keep working in offline-safe and non-OpenRouter lanes until valid OpenRouter auth is restored.

## What you can still do safely

- CLI/help and print-only inspection:
  - `python services/repo-truth-extractor/run_extraction_v5.py --help`
  - `python services/repo-truth-extractor/run_extraction_v5.py --print-routing-guide`
  - `python services/repo-truth-extractor/run_extraction_v5.py --print-prescan-guide`
  - `python services/repo-truth-extractor/run_extraction_v5.py --preset first-live --dry-run --print-config --run-id <RUN_ID>`
- Offline validator and route/trust checks:
  - `python services/repo-truth-extractor/validate_pre_live_gate_v25.py`
  - `python services/repo-truth-extractor/validate_pre_live_gate_v25.py --target-policy cost --target-phases A H D C`
  - Read `VALIDATION_VERDICT.json` for the repo/tooling verdict and `environment_summary` for live-online blocking or missing preflight evidence.
- Dry-run and cost-preview work:
  - `python services/repo-truth-extractor/run_extraction_v5.py --phase A --dry-run --print-cost-preview --run-id <RUN_ID>`
  - `python services/repo-truth-extractor/run_extraction_v5.py --preset first-live --dry-run --run-id <RUN_ID>`
- Offline hygiene and parser/contract hardening:
  - `python services/repo-truth-extractor/extraction_hygiene.py scan`
  - `pytest -q services/repo-truth-extractor/tests/test_pre_live_gate_v25.py services/repo-truth-extractor/tests/test_run_extraction_v5_prelive_hardening.py services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`

## What remains blocked or conditional

- Bounded online first-live execution is still not truthfully `GO` when the active environment lacks valid OpenRouter auth for the required strict-route models.
- Do not weaken route requirements or pretend Gemini/xAI alone satisfy the current strict bounded `A/H/D/C` route if the contract map still points those steps at OpenRouter.
- Batch-path cleanup, dry-run trust cleanup, and parser/contract hardening can continue offline, but they do not convert environment auth failure into repo readiness.

## Operator interpretation

- `GO`: repo/tooling and required validation evidence are present.
- `CONDITIONAL_GO`: repo/tooling checks passed, but live online readiness is still blocked or unverified by environment/provider evidence.
- `NO_GO`: repo/tooling or required environment inputs are still failing in a blocking way.
