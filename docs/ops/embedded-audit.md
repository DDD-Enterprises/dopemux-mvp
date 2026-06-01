---
id: ops-embedded-audit
title: Embedded Audit
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Embedded audit policy and proof contract for governance/process/schema packets.
---
# Embedded Audit

## Requirement

Governance, process, schema, prompt, proof, and authority-boundary packets require embedded audit unless the packet explicitly says otherwise and records why.

## Route Order

Tier 1 direct CLI routes:

1. AGY / Google Antigravity with Sonnet, if local help proves both invocation and model selection.
2. Claude Code CLI with Sonnet, if AGY is unavailable, unclear, or capacity-limited.
3. Claude Code CLI with Opus, if Sonnet lacks depth or capacity.
4. Gemini CLI for broad-context fallback.

Tier 2 persistent-auth bridge route:

5. PAL MCP clink with audit-safe `claude-audit` or `gemini-audit` configs, selected only when no Tier 1 route is `AVAILABLE` or `AVAILABLE_WITH_RISKS`. This includes fresh-sandbox `NOT_INSTALLED` states where direct CLI auth or installation is not present inside Codex.

Tier 3 explicit fallback:

6. Copilot no-tools fallback only when the packet and command explicitly allow fallback. Copilot clink support remains deferred.

Do not hardcode flags. Do not infer a model from branding. If model or invocation cannot be proven, use the next route or record `SKIPPED`.

Packet-specific supervisor-approved fallback auditors may be used only when the packet records the approval, bounded input, no-secret constraints, exact invocation, and resulting verdict in proof.

PAL MCP clink router classification is static config inspection only. The router must not call PAL MCP, execute host-side CLIs, or send repo content during preflight. Its route output is evidence for operator handoff, not an audit verdict.

For a PAL MCP clink audit, the operator or host-side runner must execute clink outside the Codex sandbox, capture `PAL_CLINK_AUDIT_OUTPUT.json`, and normalize that output into `AUDITOR_REPORT.md`. Embedded audit remains incomplete until the captured output is normalized.

## Independent CI Workflow

`.github/workflows/embedded-audit.yml` is the independent CI lane for embedded
audit proof emission. The workflow uses read-only repository permissions
(`contents`, `pull-requests`, `checks`, `statuses`, and `actions`) and does not
use `pull_request_target`.

The workflow checks out a trusted audit-source ref, fetches and verifies the
requested PR head SHA as data, runs static auditor-route preflight from the
trusted source checkout, and then invokes
`scripts/audit/run_embedded_audit.py` from that trusted checkout. The emitter
writes `PROOF.json` and the canonical
`proof/<packet-id>/AUDITOR_REPORT.md` report path into the uploaded
`embedded-audit-artifacts/` bundle. Preflight may fail or classify tooling as
unavailable; proof emission still runs so unavailable audit authority is
recorded explicitly instead of disappearing.

During bootstrap PRs where the trusted base ref does not yet contain the proof
emitter, the workflow emits a schema-valid `SKIPPED` proof instead of executing
the PR-head copy of the emitter.

If the requested PR head SHA cannot be fetched or verified, the workflow emits a
schema-valid `SKIPPED` proof with that integrity failure as the reason rather
than emitting a normal proof for an unverified head.

Manual dispatch uses the repository default branch as the trusted proof-authoring
checkout and treats the supplied `head_sha` only as the inspected target.

The pull-request workflow does not expose `EMBEDDED_AUDIT_TOKEN` to PR-head
code. The entrypoint never records token values, and trusted-ref callers may
record whether the expected token was present as provenance:

- `trusted_token_status: AVAILABLE` when the token is present.
- `trusted_token_status: UNKNOWN` when the token is absent or unproven.

When route evidence is unavailable, the token is absent, or PAL clink output is
missing, the emitted `embedded_audit` object is schema-valid `SKIPPED` with a
non-empty `skip_reason`. This is not a PASS verdict.

The workflow is proof-authoring authority only for the embedded-audit artifact.
PR Steward and merge/remediation engines may request audit proof but must not
author it.

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

`PASS_WITH_RISKS` is acceptable to downstream gates when the risks are recorded and no blocking findings remain. It is advisory, not a license to ignore unresolved implementation blockers elsewhere.
