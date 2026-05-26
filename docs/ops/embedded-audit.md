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

Packet-specific supervisor-approved fallback auditors may be used only when the packet records the approval, bounded input, no-secret constraints, exact invocation, and resulting verdict in proof.

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

## Review Bundle

Every non-trivial implementer run must create `proof/<PACKET_ID>/review_bundle/` as the single upload/review unit. If it is not present, proof is incomplete.

Loose `/tmp` artifacts must be copied into the review bundle or explicitly listed as excluded with a reason. The review bundle must not include secrets, tokens, credentials, private keys, raw auth headers, or local machine-sensitive files.

## Verdict Rules

- `PASS`: no blocking findings.
- `PASS_WITH_RISKS`: non-blocking risks remain and are recorded.
- `FAIL`: blocking issue found.
- `NEEDS_SUPERVISOR`: unresolved authority, security, schema, or process issue needs higher review.
- `SKIPPED`: no supported auditor executable or invocation could be proven; final packet status cannot be READY.
