---
id: TP-DCP-MCP-RO-0017
title: Acceptance Matrix And Fail-Closed Harness
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Deterministic acceptance harness and matrix for DCP multi-provider series; live gates stay NOT_RUN without dual consent.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0017

## Objective

Land the acceptance matrix and a harness that proves deterministic blocking
gates and **never** treats skipped live/provider gates as PASS.

## Live consent (explicit)

Live gates require all of:

```text
DCP_ACCEPTANCE_LIVE=1
DCP_ACCEPTANCE_LIVE_TOKEN=<non-placeholder secret>
DCP_ACCEPTANCE_LIVE_PROVIDERS=chatgpt  # or list; not none
```

Even with consent env set, this packet does **not** auto-run vendor tunnels;
operators attach redacted receipts from bounded manual runs.

## Scope

IN: matrix doc, harness module, harness tests, packet/proof.

OUT: production credentials, unrestricted public exposure, automatic provider
enablement, backend mutation.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_acceptance_harness.py
PYTHONPATH=services/dcp-readonly-facade/src uv run --frozen python -m dcp_facade.acceptance
```

## Rollback

Revert TP-0017 commits. No runtime behavior of stdio tools is required to change.
