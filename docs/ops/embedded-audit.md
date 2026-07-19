---
id: ops-embedded-audit
title: Embedded Audit
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-07-13'
next_review: '2026-10-11'
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

The workflow checks out a trusted audit-source ref, fetches the requested PR
head SHA as data, verifies it matches `refs/pull/<number>/head`, runs static
auditor-route preflight from the trusted source checkout, and invokes the
trusted-source `scripts/audit/pal_clink_runner.py` when present to capture
`PAL_CLINK_AUDIT_OUTPUT.json`. It then invokes
`scripts/audit/run_embedded_audit.py` from that trusted checkout. The emitter
writes `PROOF.json` and the canonical `proof/<packet-id>/AUDITOR_REPORT.md`
report path into the uploaded `embedded-audit-artifacts/` bundle. Preflight or
runner execution may fail or classify tooling as unavailable; proof emission
still runs so unavailable audit authority is recorded explicitly instead of
disappearing.

During bootstrap PRs where the trusted base ref does not yet contain the proof
emitter, the workflow emits a schema-valid `SKIPPED` proof instead of executing
the PR-head copy of the emitter.

If the requested PR head SHA cannot be fetched or does not match the requested
PR head ref, the workflow emits a schema-valid `SKIPPED` proof with that
integrity failure as the reason rather than emitting a normal proof for an
unverified or unrelated head.

Manual dispatch uses the repository default branch as the trusted proof-authoring
checkout and treats the supplied `head_sha` only as the inspected target after
confirming it belongs to the supplied `pr_number`.

The workflow passes `EMBEDDED_AUDIT_TOKEN` only to the trusted-source emitter
step. Bootstrap and head-integrity SKIPPED paths run without that secret.

`EMBEDDED_AUDIT_TOKEN` is proof provenance, not model-provider authentication.
The hosted runner provisions the stable Claude Code `2.1.204` package on Node
22 after PR-head integrity succeeds. Only the trusted PAL runner step receives
provider authentication as `ANTHROPIC_API_KEY`, preferring the canonical
`ANTHROPIC_API_KEY` repository secret and falling back to the legacy
`CLAUDE_API_KEY` secret name. Installation, candidate-object fetch, and proof
emission do not receive that provider credential.

The `claude-audit` client contract requires noninteractive `--print` mode,
disables built-in tools with `--tools ""`, and prevents MCP loading with
`--strict-mcp-config` and no `--mcp-config`. Safe mode and disabled session
persistence prevent repository customizations and audit-session state from
affecting later runs. Static route inspection rejects a Claude audit config
that omits these execution boundaries. If provider authentication is absent,
the runner emits a structured error and the existing hard enforcement step
keeps the audit and PR Steward readiness red.

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

## Local Claude Code / CLI route (pre-PR)

A Claude Code (or other Tier-1 CLI) session may run the embedded audit locally
against the working diff before a PR exists, instead of waiting for the CI lane.
This is a first-class route (route #2 Sonnet, route #3 Opus), independent of the
implementer as long as the auditing session is not the one that wrote the diff.
Precedent: `proof/TP-DCP-MCP-RO-0008` (Opus self/independent audit).

Procedure:

1. **Perform the audit** against the staged diff. For code packets this is a
   correctness / security / scope review; for governance / evidence / docs
   packets it is provenance integrity, allowlist and scope discipline, authority
   hygiene, and diff hygiene — recompute artifact hashes, verify inventories,
   `git diff --check`, check every staged path against the packet allowlist, and
   scan for secrets. Optionally corroborate with an independent clink run via
   `scripts/audit/pal_clink_runner.run_audit` (route resolved by
   `scripts/audit/auditor_router.select_route`); if you do, capture it in the
   review bundle and label it a leading-prompt second look, not the hard
   evidence.
2. **Author `proof/<PACKET_ID>/PROOF.json`.** The `embedded_audit` sub-object
   must conform to `schemas/proof/embedded_audit.schema.json` (see "Required
   Proof Object"). For a Claude Code route use `auditor_tool: "claude-code-cli"`
   with `auditor_model: "opus"` or `"sonnet"`, a non-empty `invocation`, and a
   `report_path` matching `^proof/<PACKET_ID>/AUDITOR_REPORT.md$`.
3. **Include the top-level fields the PR Steward gate reads**
   (`src/dopemux_pr_merge_specialist/steward_gate.py`): `head_sha` and
   `generated_at`, alongside the `embedded_audit` object:

   ```json
   {
     "head_sha": "<sha>",
     "generated_at": "<ISO-8601 UTC, e.g. 2026-07-13T07:27:09Z>",
     "embedded_audit": { "...": "schema object" }
   }
   ```

4. **Write `proof/<PACKET_ID>/AUDITOR_REPORT.md`** and populate
   `proof/<PACKET_ID>/review_bundle/` (see "Review Bundle").
5. **Validate:**
   `python scripts/audit/validate_audit_proof.py proof/<PACKET_ID>/PROOF.json`
   and the `Validate proof bundle embedded_audit schema` pre-commit hook.

Scope and staleness honesty: `pr-steward gate --audit-proof` re-checks the proof
at the PR head with a 1-hour TTL (`steward_gate` `ttl_seconds=3600`) and
cross-checks `head_sha` against a `MERGE_READINESS.json` produced by
`pr-steward intake` against a real PR. A pre-PR local audit therefore leaves the
PR-scoped gate `NOT_RUN`; regenerate the proof and re-pin it to the PR head SHA
before the FINALIZATION gate, and record that explicitly rather than implying
gate readiness.

## Local signed attestation (CI acceptance without provider credentials)

When the trusted CI job cannot execute any auditor CLI (no provider
credentials provisioned on the runner), the `independent embedded audit` check
can accept a **locally executed** audit through a signed, exact-head-bound
attestation. Implemented by `scripts/audit/local_audit_acceptance.py` and the
`Evaluate local signed audit attestation` workflow step; consumed by the proof
emitter via `--local-attestation-json`.

Acceptance is fail-closed. ALL of the following must hold:

1. The PR head carries `proof/pr_merge/embedded-audit/pr-<N>/PROOF.json` and a
   detached OpenSSH signature `PROOF.json.sig` over those exact bytes,
   namespace `dopemux-embedded-audit`.
2. The signature verifies against
   `config/audit/embedded-audit-allowed-signers` **taken from the trusted ref
   (main)** — keys added on the PR branch have no effect.
3. The signed proof names this `repo` and `pr_number`, and its `head_sha`
   (the audited commit) is an ancestor of the PR head where the diff between
   them touches **only** the proof directory itself (proof-only delta: the
   commit adding the proof is the sole change on top of the audited code).
4. The local `embedded_audit` object is a passing verdict
   (`PASS`/`PASS_WITH_RISKS`) and valid against
   `schemas/proof/embedded_audit.schema.json` — including the
   `auditor_tool`/`auditor_model` enums. (`report_path` is overridden by the
   trusted emitter.)
5. The least-privilege `EMBEDDED_AUDIT_TOKEN` is still present in the trusted
   run, and the CI auditor produced **no real verdict** — a CI-executed
   `PASS`/`PASS_WITH_RISKS`/`FAIL` always outranks the attestation.

The emitted proof records the substitution explicitly:
`provenance.audit_source = "local-signed-attestation"` plus a
`provenance.local_attestation` object (principal, audited SHA, proof path),
and an appended `remaining_risks` entry naming the signer. Steward summaries
and artifacts therefore always show when a run was locally attested.

**Trust model (stated plainly):** a valid signature proves that a holder of an
allow-listed private key attests this exact code was audited locally. It is an
operator attestation with cryptographic code-binding — not an independently
executed CI audit. Signer changes go through reviewed PRs to main.

One-time signer setup:

```bash
ssh-keygen -t ed25519 -N '' -f ~/.ssh/dopemux_audit_signing \
  -C "dopemux embedded-audit signing"
# add the printed public key line to config/audit/embedded-audit-allowed-signers
# via a reviewed PR to main (instructions in that file)
```

Per-PR flow (after the local pr-merge audit writes the proof):

```bash
scripts/audit/sign_local_audit_proof.sh <pr-number>   # validates + signs
git add proof/pr_merge/embedded-audit/pr-<N>/
git commit -m "proof(audit): signed local embedded-audit attestation for PR <N>"
git push   # must be the only change on top of the audited head_sha
```

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
