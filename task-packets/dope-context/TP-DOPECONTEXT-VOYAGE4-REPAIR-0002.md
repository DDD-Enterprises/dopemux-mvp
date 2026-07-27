---
id: TP-DOPECONTEXT-VOYAGE4-REPAIR-0002
title: Repair Voyage vector compatibility and collection migration
type: task-packet
owner: "@hu3mann"
last_review: 2026-07-26
next_review: 2026-10-24
status: AUTHORIZED_FOR_IMPLEMENTATION
---

# TP-DOPECONTEXT-VOYAGE4-REPAIR-0002

## Objective

Repair the merged dope-context Voyage modernization (PR #1112) before first
deployment so index and query vector spaces match, incompatible profiles cannot
silently share a Qdrant collection, and contextual rollback is single-variable.

## Blocking findings repaired

| ID | Repair |
|----|--------|
| F-001 | Code `content_vec` query uses contextualized endpoint + same model as index |
| F-002 | Versioned collection identity from full profile fingerprint |
| F-003 | Single `DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL` for all contextual paths |

## High-priority repairs

F-004, F-006, F-007, F-010, F-017 and bounded items F-008–F-015 as implemented
in the repair branch.

## Rollback

```bash
export DOPE_CONTEXT_CONTEXTUAL_EMBED_MODEL=voyage-context-3
```

## Deployment

**NOT_RUN** in this packet.
