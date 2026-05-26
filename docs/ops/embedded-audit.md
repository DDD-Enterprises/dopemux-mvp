---
id: ops-embedded-audit
title: Embedded Audit
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Embedded audit policy and proof contract for governance/process/schema packets.
---
# Embedded Audit

## Requirement

Governance, process, schema, prompt, proof, and authority-boundary packets require embedded audit unless the packet explicitly says otherwise and records why.

## Route Order

1. AGY / Google Antigravity with Sonnet, if local help proves both invocation and model selection.
2. Claude Code CLI with Sonnet, if AGY is unavailable, unclear, or capacity-limited.
3. Claude Code CLI with Opus, if Sonnet lacks depth or capacity.
4. Gemini CLI for broad-context fallback.

Do not hardcode flags. Do not infer a model from branding. If model or invocation cannot be proven, use the next route or record `SKIPPED`.

## Required Proof Object

The proof object must conform to `schemas/proof/embedded_audit.schema.json` and record:

- whether audit was required
- status
- auditor tool
- auditor model
- exact invocation
- exit code
- report path
- findings
- fixes applied
- remaining risks
- skip reason when skipped

## Verdict Rules

- `PASS`: no blocking findings.
- `PASS_WITH_RISKS`: non-blocking risks remain and are recorded.
- `FAIL`: blocking issue found.
- `NEEDS_SUPERVISOR`: unresolved authority, security, schema, or process issue needs higher review.
- `SKIPPED`: no supported auditor executable or invocation could be proven; final packet status cannot be READY.
