# TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001 Implementation Notes

## Decision

`PROPOSED`: approve the exact embedded-auditor model identifier
`gemini-3.1-pro-preview` when used through AGY with explicit model-selection
proof.

## Observed Evidence

- Google documents the API model identifier as `gemini-3.1-pro-preview`.
- Antigravity CLI documents `agy` as the executable and supports explicit
  `--model` selection plus noninteractive `--print` mode.
- The existing canonical schema already allows `auditor_tool: "agy"` and the
  backward-compatible generic `auditor_model: "gemini"` value.
- The existing CI workflow has no AGY authentication route and already supports
  signed local audit attestation when provider credentials are unavailable.

## Changes

- Added `gemini-3.1-pro-preview` to the canonical `auditor_model` enum.
- Added a regression test for the exact approved identifier, rejection of the
  near-match `gemini-3.1-pro`, and compatibility of generic `gemini`.
- Updated audit policy and proof-format documentation with exact invocation,
  no-fallback evidence, and local-attestation boundaries.
- Added a bounded task packet. No workflow, secret, signer, PR Steward, or
  local-attestation implementation changed.

## Validation

### OBSERVED

- GitHub accepted all file writes on branch
  `codex/approve-agy-gemini-3-1-pro-audit`.
- Changed paths are within the task-packet allowlist.
- At audited head `8f2c009c35309c4aad371d17568528b61b84523d`:
  - `CI_TESTS=PASS`
  - `INDEPENDENT_AUDIT=NEEDS_SUPERVISOR`
  - `PR_STEWARD=FAIL`
  - `LOCAL_AGY_SELECTOR_PROOF=NOT_RUN`
- The local AGY installation reported version `1.1.8`; `agy models` did not
  list `gemini-3.1-pro-preview`. Per this packet's stop condition, no
  substitute selector and no exact-model print-mode invocation were used.

### NOT_RUN

- `python -m json.tool schemas/proof/embedded_audit.schema.json`
- `python -m pytest tests/audit/test_audit_proof.py tests/audit/test_agy_gemini31_model.py -q`
- scoped documentation validation
- `git diff --check`
- exact-model AGY print-mode invocation
- fresh independent embedded audit and PR Steward readiness for any successor
  head; this document itself changes the former audited head.

These remain merge blockers until current-head CI and local AGY evidence are
captured.

## Bootstrap Audit Rule

This admission PR must be audited under the schema currently trusted on `main`.
Its local signed proof must use `auditor_tool: "agy"` and
`auditor_model: "gemini"`, while the exact invocation and report prove that
`gemini-3.1-pro-preview` ran without fallback. After this PR merges, later proofs
may record `auditor_model: "gemini-3.1-pro-preview"` directly.

## Rollback

Revert the approval commit. Existing generic `gemini` proofs remain valid.
Exact-model proofs created after approval would no longer validate and must not
be accepted after rollback.
