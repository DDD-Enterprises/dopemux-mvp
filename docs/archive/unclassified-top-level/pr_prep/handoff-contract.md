---
id: HANDOFF_CONTRACT
title: Handoff Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Handoff Contract for pr-prep-specialist to pr-merge-specialist handoff.
---
# Handoff Contract

This document defines the exact payload that `pr-prep-specialist` delivers to `pr-merge-specialist`.

## PR_HANDOFF_BUNDLE.json Requirements

The bundle must guarantee that `pr-merge-specialist` receives:

### Required Identity
- `repo`: Repository name.
- `current_branch`: The head branch being merged.
- `base_branch`: The target branch.
- `pr_id` / `pr_url`: Populated if created.

### Required Content
- `title`: Final chosen title.
- `body_path`: Path to the generated body markdown.
- `final_prep_decision`: The synthesized validation decision.
- `validation_summary`: A sub-object detailing deterministic/consensus outcomes.

### Required Risk/Context
- `risk_hint`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `high_risk_handoff_required`: Boolean flag.
- `adjacent_work_decision`: Context on uncommitted local overlaps.
- `obligation_summary`: Status of docs, changelogs, migrations.
- `warnings`: Array of explicit warnings.

### Required Next Step
Must be exactly one of:
- `MERGE_SPECIALIST_NORMAL_FLOW`
- `MERGE_SPECIALIST_DRAFT_FLOW`
- `MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW`
- `NO_HANDOFF_BLOCKED`
