---
id: TP-DOPECONTEXT-CTX3-0001
title: Tp Dopecontext Ctx3 0001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-26'
last_review: '2026-02-26'
next_review: '2026-05-27'
prelude: Tp Dopecontext Ctx3 0001 (explanation) for dopemux documentation and developer
  workflows.
---
# Task Packet: TP-DOPECONTEXT-CTX3-0001 · Dope-Context · Spec + Contracts + Contract Tests

## Objective
Add the v1 docs contextual embedding spec and machine-checkable schema contracts with offline tests.

## Scope
IN:
- `/Users/hue/code/dopemux-mvp/docs/03-reference/dope-context/DOPE_CONTEXT_DOCS_CONTEXTUAL_EMBEDDING_v1.md`
- `/Users/hue/code/dopemux-mvp/contracts/dope-context/*.schema.json`
- `/Users/hue/code/dopemux-mvp/services/dope-context/tests/contract/test_dope_context_contracts.py`

OUT:
- Runtime indexing/search behavior changes

## Acceptance
- Contract tests pass offline.
- Root hygiene accepts `contracts/`.
