---
id: README
title: Readme
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-22'
last_review: '2026-06-22'
next_review: '2026-09-20'
prelude: Readme (reference) for dopemux documentation and developer workflows.
---
# OpenClaw DCP Routing Contracts Pointer

This directory is a documentation pointer only.

The canonical mutable machine-contract source for OpenClaw/DCP routing is:

```text
contracts/openclaw-dcp-routing/
```

Do not edit or re-create routing schemas, policy YAML, route examples, benchmark
fixtures, proof contracts, runner adapter contracts, or provider probe contracts
under this docs path. Update `contracts/openclaw-dcp-routing/` instead.

## Provenance

- PR #926 introduced the earlier docs-path OpenClaw/DCP routing contract bundle.
- PR #931 introduced the first-class `contracts/openclaw-dcp-routing/` tree.
- `TP-DMX-ROUTING-CONTRACT-CANONICALIZATION-0001` resolves the duplicate
  mutable policy surface by making `contracts/openclaw-dcp-routing/` canonical.

## Authority

The contracts tree remains contracts-only. It does not enable runtime routing,
provider calls, OpenClaw execution, OpenRouter execution, benchmark execution,
or production/high-trust route authorization by itself.
