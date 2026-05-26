---
id: prompt-pr-steward-summary
title: PR Steward Summary Prompt
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Summary prompt for check-only PR Steward readiness output.
---
# PR Steward Summary Prompt

Summarize PR readiness from harvested GitHub and proof artifacts.

Required output:

- PR URL, base, head branch, head SHA
- changed files and commits summary
- review item counts by disposition
- unresolved blocking threads
- unknown reviewers/bots
- failed, cancelled, missing, or pending required checks
- proof freshness and embedded audit status
- `MERGE_READINESS` verdict: READY, NOT_READY, or NEEDS_SUPERVISOR
- reason second GPT-5.5 review is skipped or required

Do not mutate GitHub state. Do not claim readiness if any item is unclassified.
