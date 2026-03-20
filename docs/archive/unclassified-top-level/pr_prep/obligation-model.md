---
id: OBLIGATION_MODEL
title: Obligation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Obligation Model (explanation) for dopemux documentation and developer workflows.
---
# Obligation Model

## Definition
An "Obligation" is a requirement for supporting artifacts or metadata that must accompany a code change to ensure it is complete and maintainable.

## Domains
- **Docs**: Technical documentation, API references, or user guides.
- **Changelog**: Human-readable history of changes.
- **Migration Notes**: Instructions for schema or data migrations.
- **Linked Context**: References to external issues, design documents, or ADRs.

## States
- `NOT_REQUIRED`: No evidence suggests this obligation is needed.
- `REQUIRED_PRESENT`: Obligation is required and appears to be satisfied.
- `REQUIRED_MISSING`: Obligation is required but no satisfying evidence was found.
- `PRESENT_BUT_WEAK`: Evidence found but may be insufficient (e.g., empty migration note).
- `UNKNOWN_REQUIRES_REVIEW`: Evidence is ambiguous; human intervention needed.

## Severity
- `INFO`: Minor advisory.
- `LOW`: Required but low risk if missing.
- `MEDIUM`: Expected; missing will cause a warning.
- `HIGH`: Critical for review; missing will likely block PR creation.
- `CRITICAL`: Mandatory; missing will definitely block handoff.
