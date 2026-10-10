---
id: FEATURE_FLAG_MATRIX
title: Feature Flag Matrix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Feature Flag Matrix (explanation) for dopemux documentation and developer
  workflows.
---
# Feature Flag Matrix

## Tier Definition

| Feature | Tier 0 | Tier 1 | Tier 2 | Tier 3 |
| :--- | :---: | :---: | :---: | :---: |
| **Queue Scan** | ON | ON | ON | ON |
| **Remediation Planning** | ON | ON | ON | ON |
| **Local Verification** | OFF | ON | ON | ON |
| **Metadata Hygiene** | OFF | ON | ON | ON |
| **PR Body Mutation** | OFF | ON | ON | ON |
| **Review Replies** | OFF | OFF | ON | ON |
| **Thread Resolution** | OFF | OFF | ON | ON |
| **Queue Mutation** | OFF | OFF | OFF | ON |

## Default Settings (v0.1.0)
The global default is **Tier 0** (Advisory Only). Pilot repos must explicitly opt-in to Tier 1 via repo-local policy.
