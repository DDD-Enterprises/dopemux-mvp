---
id: REF-DCP-RUNNER-CAPABILITY-MATRIX
title: Runner Capability Matrix (0009)
type: reference
owner: Control Tower | Current
last_review: 2026-10-03
next_review: 2026-11-03
author: '@hu3mann'
date: '2026-10-03'
prelude: Runner Capability Matrix (0009) (reference) for dopemux documentation and
  developer workflows.
---
# Runner Capability Matrix (0009)

Non-authoritative inventory of local runner CLIs.

## Global flags

| Flag | Value |
|---|---|
| global_invocation_authorized | **false** |
| global_mutation_authorized | **false** |
| global_paid_inference_authorized | **false** |

## Source

- Config: `config/dcp/runner_capabilities.json`
- Schema: `schemas/dcp/runner_capability_registry.schema.json`
- Loader: `src/dopemux/dcp/runner_capability_registry.py`

## Non-claims

- Install presence ≠ authorization
- Version text from `--version` is observational only
- No runner may be invoked from DCP via this registry
