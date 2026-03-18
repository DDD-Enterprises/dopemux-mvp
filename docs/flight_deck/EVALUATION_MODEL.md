---
id: EVALUATION_MODEL
title: Evaluation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Evaluation Model (explanation) for dopemux documentation and developer workflows.
---
# Flight Deck Evaluation Model

## Overview
This document defines the methodology for evaluating the unified interactive flight deck as a holistic subsystem. The goal is to determine if the combination of mission intelligence, live synthesis, and tactical controls provides a safe, materially useful operator experience.

## Evaluation Dimensions

### 1. Operator Utility
- **Task Completion Speed**: Does the guided sequencing reduce the time from triage to sign-off?
- **Cognitive Load**: Do the Spaceage UX summaries make state and blockers obvious at a glance?
- **Acceptance/Override Rates**: Are operators accepting the synthesized patches and thread syncs, or routinely overriding them?

### 2. Auto-Apply Safety
- **Risk Filter Accuracy**: Did the LLM correctly classify risk/complexity for auto-apply decisions?
- **Rollback Events**: Were any auto-applied patches manually reverted by the operator?
- **Incident Frequency**: Did any `INJECT_SAFE` action overwrite custom repo content destructively?

### 3. Continuous Gating Value
- **Signal vs. Noise**: Does the automatic refresh correctly clear blockers (e.g., thread counts dropping after sync)?
- **State Thrashing**: Did the re-evaluation incorrectly cycle a PR back to `BLOCKED` after a valid mitigation?

## Methodology
- **Evidence Aggregation**: Systematic rollup of Tranche 22 logs (Sign-offs, Case Usage, Synthesis Prompts).
- **Friction Analysis**: Review of any `REJECT` commands or abort sequences (`Q` during patch).
