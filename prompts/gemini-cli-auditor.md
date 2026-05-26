---
id: prompt-gemini-cli-auditor
title: Gemini CLI Auditor
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Broad-context embedded auditor prompt for Gemini CLI fallback.
---
# Gemini CLI Auditor

Perform a broad-context read-only audit of the current Dopemux packet diff.

Check:

- claim labels are used where needed
- governance docs do not overclaim runtime behavior
- schemas are parseable and fail-closed
- PR Steward remains check-only
- embedded audit proof is present
- unknown reviewers/bots and unclassified items block readiness

Return PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR with evidence.
