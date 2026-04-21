---
id: docs__DMPX IMPORT__dopemux-docs__architecture__09-decisions__ADR-013-data-classification
title: Docs  Dmpx Import  Dopemux Docs  Architecture  09 Decisions  Adr 013 Data Classification
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-20'
last_review: '2026-04-20'
next_review: '2026-07-19'
prelude: Docs  Dmpx Import  Dopemux Docs  Architecture  09 Decisions  Adr 013 Data
  Classification (explanation) for dopemux documentation and developer workflows.
---
# ADR: Data Classification & Residency

Status: Accepted
Date: 2025-09-17

Decision (Proposed)
- Adopt 4-level classification (Public, Internal, Sensitive, Restricted); support optional residency constraints (e.g., EU-only) via provider selection and storage policies.

Context
- Guides redaction and provider routing; some users require geographic controls.

Alternatives
- Single-level policy; per-project custom taxonomy; always-local storage.

Consequences
- Tagging and policy evaluation required across artifacts, memory, and logs; provider selection must honor residency.

Open Questions
- Which levels apply by default, and do we enforce residency by default?

Links
- V4 Security & Privacy; V3 Memory & Retrieval

Sources: user clarifications (Q5: not sure)
