---
id: ALIGNMENT_SCORING
title: Alignment Scoring
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Alignment Scoring (explanation) for dopemux documentation and developer workflows.
---
# PR Template Alignment Scoring

## Overview
Alignment scoring provides a deterministic quantitative measure of how well a repository's PR template supports the skill's enforcement model.

## 1. Section Weights
The base total weight is 100 when high-risk notes are required, and 95 otherwise.

| Section | Weight | Severity |
| :--- | :---: | :--- |
| **Verification** | 20 | HIGH |
| **Risks** | 15 | HIGH |
| **Rollback** | 15 | HIGH |
| **Summary** | 15 | MEDIUM |
| **Context** | 10 | MEDIUM |
| **Reviewer Notes** | 10 | MEDIUM |
| **Checklist** | 10 | HIGH |
| **High-Risk Integration Notes** | 5 | MEDIUM (Conditional) |

## 2. Section Status Multipliers
The following multipliers are applied to the section weight based on detected sufficiency:

- **PRESENT_AND_SUFFICIENT**: 1.00
- **ALIASED_SUFFICIENT**: 0.95
- **PRESENT_BUT_INSUFFICIENT**: 0.40
- **UNKNOWN**: 0.20
- **MISSING**: 0.00

## 3. Checklist Scoring Formula
The checklist is scored by represented intent count:
`checklist_multiplier = matched_intents / expected_intents`
- **Normal PR**: 7 expected intents.
- **High-Risk PR**: 8 expected intents.

## 4. Normalization
`normalized_score = round((sum(section_scores) / applicable_total_weight) * 100)`

## 5. Hard-Blocker Overrides
After the numeric calculation, the following downgrades are enforced regardless of score:

- **Missing Verification/Risks/Rollback**: max state = `DRIFTED`
- **Missing Checklist**: max state = `PRESENT_BUT_WEAK`
- **Multiple-Template Ambiguity**: force state = `AMBIGUOUS`
- **Mostly Placeholders**: max state = `PRESENT_BUT_WEAK`

## 6. Final State Mapping
1. Calculate `normalized_score`.
2. Map to `raw_band_state`:
    - 90–100: `ALIGNED`
    - 70–89: `PARTIALLY_ALIGNED`
    - 50–69: `PRESENT_BUT_WEAK`
    - 1–49: `DRIFTED`
    - 0: `MISSING`
3. Apply Hard Blockers: `final_state = min(raw_band_state, blocker_max_state)`.
