# Replacement audit proof validation evidence

## Audit identity and output

- Exactly one authorized replacement inference ran.
- Runner/version: `copilot-cli 1.0.82-0`.
- Billing mode: `PLAN_BACKED`; metered/API route not used.
- Requested, configured, selected, current, request, response, and proxy model:
  `claude-sonnet-4.6`.
- Observed provider: `github`; provider attestation: `UNKNOWN`.
- One inference request; zero model-change events; fallback observed: `false`.
- Zero tool requests, execution events, and OTel tool-call sum; zero code changes.
- Strict parser accepted exactly one bare JSON object with exact head/tree,
  `17` paths, required identity keys, eight required relationship results, no
  blocking findings, and four non-blocking risks.
- Normalized `audit_result` in `AUDIT_RUN_RECEIPT.json` matched the scan-clean
  Copilot session export exactly.

## Deterministic proof closure

- `python scripts/audit/validate_audit_proof.py
  proof/TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002/PROOF.json`: exit `0`, `1/1 PASS`.
- R2 packet validation against
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`: exit `0`.
- SHA-256 and Git blob recomputation for R2 packet, current G0 packet,
  authority record, and late R1 proof: exit `0`; all values match
  `PROOF.json`.
- Canonical replacement delta: `7` paths, all under
  `proof/TP-DMX-GOV-G0-LITE-PR1282-REPAIR-002/**`.
- Redacted gitleaks directory scan on final canonical bundle: exit `0`, no
  retained leaks.
- Direct changed-contract validation against an exact commit object carrying
  the final staged tree, with content/audited head
  `79404f3929c47fe09434ac07a36b936190282b56`: exit `0`, `status=PASS`,
  `max_lane=L0`, `proof_only=True`, model audit `NOT_REQUIRED`.
- Exact-file pre-commit: exit `0`; all applicable hooks passed.
- Detached canonical `PROOF.json.sig` verifies for allowed principal
  `hue@local` under namespace `dopemux-embedded-audit`.
- `git diff --check`: exit `0`.

After canonical commit, PR-scoped proof is regenerated and signed separately,
then the same proof-only ancestry, local-audit-acceptance, schema, signature,
secret, allowlist, changed-contract, pre-commit, and diff gates are rerun at
final exact head. No content audit is rerun for proof-only successors.

## Evidence retention

Retained replacement artifacts passed redacted secret scan. One generic-key
signature existed only in raw session events; exact raw file was deleted after
its artifact hash and sanitized evidence predicates were recorded outside repo.
Secret value was not inspected. Repository proof retains no raw transcript,
raw CLI log, raw events, secret value, or provider credential.

READY, dispatch, merge, activation, Task Orchestrator, content, authority,
Task Packet, and INDEX mutations remain forbidden.
