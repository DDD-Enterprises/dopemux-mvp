---
id: CONFIDENCE_MODEL
title: Confidence Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Confidence Model (explanation) for dopemux documentation and developer workflows.
---
# Confidence Model

## Confidence Levels
All arbitration roles must provide a confidence level for their primary findings or recommendations.

| Level | Definition | Typical Use |
| :--- | :--- | :--- |
| **HIGH** | Evidence is unambiguous and comprehensive. | Safe mechanical or clearly addressed semantic fixes. |
| **MEDIUM** | Evidence supports the conclusion but has minor gaps or risks. | Typical synthesized merge proposals. |
| **LOW** | Evidence is sparse or contradictory. | Complex overlaps or conflicting intent cases. |
| **INSUFFICIENT** | Required context is missing or inaccessible. | Triggers a `DEFER_TO_HUMAN` decision. |

## Confidence Rationale
Each level must be accompanied by a `confidence_reason` citing specific sections of the evidence bundle.
