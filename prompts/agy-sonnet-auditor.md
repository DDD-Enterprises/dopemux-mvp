---
id: prompt-agy-sonnet-auditor
title: AGY Sonnet Auditor
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Embedded auditor prompt for AGY or Google Antigravity when Sonnet invocation is proven locally.
---
# AGY Sonnet Auditor

Audit the current packet diff for governance, schema, prompt, proof, and authority-boundary correctness.

Return Markdown with:

- verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR
- blocking findings
- non-blocking risks
- files reviewed
- validation evidence reviewed
- authority-boundary concerns
- whether second GPT-5.5 review can be skipped

Do not edit files. Do not infer AGY model settings unless local help or invocation output proves them. If Sonnet invocation is not proven, report NEEDS_SUPERVISOR or use a fallback auditor.
