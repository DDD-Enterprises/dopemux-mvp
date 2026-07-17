---
id: TP-DCP-MCP-RO-0016
title: Multi-Provider Setup And Rollback Docs
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-16'
prelude: Provider setup, disable/rollback, and source-date ledgers for the DCP multi-provider series.
last_review: '2026-07-16'
next_review: '2026-10-14'
---
# TP-DCP-MCP-RO-0016

## Objective

Document how operators configure ChatGPT, Grok, Gemini, and local agents
against the DCP facade using placeholders only, with disable/rollback and
command/source-date verification.

## Scope

IN: provider setup guide, disable/rollback, command ledger, source-date ledger,
example validation tests, packet/proof/index/BUILD_SERIES.

OUT: live provider creation, real credentials, tunnels, hostnames, private
paths, code behavior changes outside docs/tests.

## Validation

```text
uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_provider_docs_examples.py
uv run --frozen pytest -q services/dcp-readonly-facade/tests
```

## Rollback

Revert the TP-0016 docs/test commits only.
