---
id: OPERATIONAL_LEARNING_MODEL
title: Operational Learning Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Operational Learning Model (explanation) for dopemux documentation and developer
  workflows.
---
# Operational Learning Model

## Overview
The PR Merge Specialist uses an append-only, auditable learning loop to bridge the gap between structural validation and real-world performance.

## Data Sources
1. **Adoption Metrics**: Rollout tiers and invocation frequency.
2. **Override Ledger**: Explicit human disagreements with automated decisions.
3. **Outcome Attribution**: Cross-referencing engine decisions with eventual GitHub state (e.g., was the PR merged?).
4. **Validation Proofs**: Per-run artifacts (`READINESS_DECISION.json`, etc.).

## Learning Pipeline
1. **Capture**: Record raw events and overrides in `OVERRIDE_LEDGER.jsonl`.
2. **Classify**: Map events to the `OUTCOME_TAXONOMY`.
3. **Analyze**: Identify patterns of over-blocking or missed escalations.
4. **Recommend**: Generate `POLICY_TUNING_RECOMMENDATIONS.json`.

## Constraints
- **Non-Self-Modifying**: Policy updates require human review and a new PR.
- **Evidence-First**: Recommendations must cite specific Run IDs and artifact paths.
- **Privacy**: Summarize by category; avoid persisting PII or sensitive code snippets in learning reports.
