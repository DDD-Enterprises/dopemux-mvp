---
audit_id: TP-DMX-GOV-G0-LITE-PR1282-AUDIT-EVIDENCE-RECOVERY-001-A1-FINAL-L2
runner: copilot-cli
runner_version: 1.0.82-0
requested_model: claude-sonnet-4.6
observed_execution_model: claude-sonnet-4.6
subject_head: 79404f3929c47fe09434ac07a36b936190282b56
subject_tree: 324348b70013207d908e3f5af66302336dfd99e9
verdict: PASS_WITH_RISKS
---

# Replacement final L2 audit report — PR #1282 R2

## Route and subject

- Runner: `copilot-cli` `1.0.82-0`
- Billing mode: `PLAN_BACKED`
- Requested/configured/observed execution model: `claude-sonnet-4.6`
- Observed provider: `github`
- Response-claimed/proxy-reported model: `claude-sonnet-4.6`
- Provider-attested model: `UNKNOWN`
- Fallback allowed/observed: `false` / `false`
- Session: `12820000-0000-4000-8000-000000000004`
- Inference requests: `1`
- Tools executed: `0`
- Audited head: `79404f3929c47fe09434ac07a36b936190282b56`
- Audited tree: `324348b70013207d908e3f5af66302336dfd99e9`
- Base: `c7bc2fb479d7386825df73e028acdce723ee3388`
- Expected/observed changed paths: `17` / `17`

Runtime evidence independently records one request whose selected, current,
request, response, and proxy model are all `claude-sonnet-4.6`; no model-change
event occurred. Session events and OTel record zero tool calls. This proves
actual runtime model selection and no fallback for this replacement audit.
Provider attestation remains `UNKNOWN`, as permitted.

## Relationship results

- G0 packet/authority exact bindings: `PASS`.
- `SUPERSET=STOP_FOR_SUPERVISOR_ADJUDICATION`: `PASS`.
- Late R1 proof-root closure and historical/current byte separation: `PASS`.
- Authority ceiling and fail-closed behavior: `PASS`.
- No READY authority: `PASS`.
- No dispatch authority: `PASS`.
- No merge authority: `PASS`.
- No activation authority: `PASS`.

## Findings

Blocking findings: none.

Non-blocking risks, preserved exactly from the machine-readable audit result:

1. `NB-01` (`LOW`, `ACCEPTED_RISK`) — **Historical G0 packet SHA split in R1 audit receipts.** R1 audit bundle records `g0_packet_sha256=cf3370d...` while current authority record, `TP-DMX-GOV-G0-LITE-PR1282-REPAIR-001/PROOF.json`, and `SUBJECT_BINDING.md` record `6d6e9d5e...`. Properly labeled as historical R1 audit lineage in `AUDITOR_REPORT` finding F1 (`RESOLVED`). Late-repair-closure framework explicitly acknowledges this split.
2. `NB-02` (`LOW`, `ACCEPTED_RISK`) — **Authority record SHA split between R1 and R2 proof bundles.** R1 receipts record `authority_record_blob=d43488cb...` (pre-repair); R2 proof records blob `ae03821e...` (current, matches diff). Consistent with late-repair lineage semantics.
3. `NB-03` (`INFO`, `ACCEPTED_RISK`) — **R2 final independent audit deferred pending early review stabilization.** `remaining_risks` explicitly states R2 substantive changes not covered by R1 receipt. `TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002.json` S2 requires early Codex and Copilot review routes to stabilize before final R2 audit. Not a defect for this audit-evidence-recovery subject. This describes audited pre-replacement proof state; replacement audit recorded here now supplies final independent judgment.
4. `NB-04` (`INFO`, `ACCEPTED_RISK`) — **Proxy-reported and provider-attested auditor model identities remain UNKNOWN.** `proxy_reported_model` and `provider_attested_model` are `UNKNOWN` in R1 audit receipt. Consistently recorded across `PROOF.json`, `COPILOT_RUN_RECEIPT.json`, and `AUDITOR_REPORT`. Governance accepts this when other identity layers are confirmed. This is historical R1 evidence only; replacement audit proxy reports `claude-sonnet-4.6` while provider attestation remains allowed `UNKNOWN`.

## Evidence retention boundary

Raw session events were deleted after a redacted secret scan reported one
generic-key signature. Secret value was not inspected. Retained prompt,
machine-readable audit result, runtime receipt, OTel summary, usage summary,
and session export were scanned with no retained leaks. Repository bundle keeps
only sanitized prompt, result, receipt, subject, validation, and review
evidence; no raw log or secret value is retained.

Prior inadmissible audit artifacts carry no judgment into this verdict.
Content remained frozen; no fixes were applied after audit.

## Verdict

`PASS_WITH_RISKS`
