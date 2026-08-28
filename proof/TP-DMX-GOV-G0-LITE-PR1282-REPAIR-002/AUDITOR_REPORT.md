---
audit_id: TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002-FINAL-L2
runner: AGY
model_selector: gemini-3.1-pro-high
subject_head: 79404f3929c47fe09434ac07a36b936190282b56
subject_tree: 324348b70013207d908e3f5af66302336dfd99e9
verdict: PASS
---

# Final L2 audit report — PR #1282 R2

## Route and subject

- Runner: AGY
- Exact requested selector: `gemini-3.1-pro-high`
- Mode: `plan`, sandboxed, high effort
- Billing mode: `PLAN_BACKED`
- Conversation: `3dcabcf7-00c4-431d-9393-28fd53b659a3`
- Exit code: `0`
- AGY status: `SUCCESS`
- Audited head: `79404f3929c47fe09434ac07a36b936190282b56`
- Audited tree: `324348b70013207d908e3f5af66302336dfd99e9`
- Comparison start: `1ede09aeb71d98a6f9464ec2725f9f5660c2b4b7`

Exact selector plus successful exact-model invocation are retained. No stronger
provider-level model or fallback claim is inferred; provider attestation remains
`UNKNOWN`.

## Independent checks retained by controller

- Exact head, clean worktree, and repository identity: `PASS`.
- R2, R1, and controlling G0 Task Packet schemas: `PASS`.
- Late R1 proof validator: `PASS`.
- Docs validator and frontmatter guard: `PASS`.
- Changed-contract preflight: `PASS`, L2.
- Diff check: `PASS`.
- R2 changed-path inventory: `PASS`, eight paths, all allowlisted.
- Current G0 packet SHA-256/blob binding: `PASS`.
- Current authority-record SHA-256/blob binding: `PASS`.
- Six-way overlap actions, including
  `SUPERSET=STOP_FOR_SUPERVISOR_ADJUDICATION`: `PASS`.
- Late R1 proof identity and current-versus-historical byte separation: `PASS`.
- INDEX remains `Active / merge blocked`: `PASS`.
- Instruction-like candidate content was treated as untrusted data and
  acknowledged: `PASS`.

## Findings

- Blocking findings: none.
- Non-blocking findings retained by controller: none.
- Fixes applied after audit: none. Content remained frozen.

## Evidence retention boundary

Raw AGY transcript and CLI log are not retained. They were deleted after
unrelated local sensitive configuration appeared. Canonical bundle contains
sanitized prompt, receipt, subject binding, deterministic validation, and review
evidence only. No credential value is repeated.

## Verdict

`PASS`
