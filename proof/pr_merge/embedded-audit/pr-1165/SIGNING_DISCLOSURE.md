# Signing disclosure — PR #1165 local attestation (replacement proof, round 3)

This disclosure supersedes the one published with the previous signed proof, which was
superseded when a reviewer found that the trusted local-attestation gate did not enforce
the very trust contract this PR establishes. That defect was repaired, the tree was
re-audited, and the proof was regenerated from the new audit evidence.

## What the signature does and does not prove

The detached OpenSSH signature over `PROOF.json` proves that a holder of an allow-listed
private key attests that these exact audit bytes correspond to the audited head. It is an
**operator attestation**, not an independent third-party audit, and it is not evidence that
any provider executed anything in GitHub CI.

## Independence of the audit itself

The substantive audit was performed by a **different runner and model** from the producer:

| Role | Runner | Model |
|---|---|---|
| Producer (authored the repair) | Claude Code | claude-opus-5 |
| Independent auditor | AGY (Google Antigravity CLI v1.1.11) | `gemini-3.1-pro-high` |

The auditor ran read-only (`--mode plan`), in fresh single-turn sessions, and did not
execute repository code. Three rounds were run:

| Round | AUDITED_TREE | Verdict |
|---|---|---|
| 1 | `491e59a8686b50782aee5b1bc245eb9c36dd2fd2` | FAIL — three risks |
| 2 | `02c915d8006ca5cddba9247ba9bf440581be7257` | PASS — zero risks |
| 3 (controlling) | `d2d3ff808e80e6d6a490616d4ff2341a63c29d86` | **PASS** — zero risks, 11/11 |

Rounds 1 and 2 are historical evidence only. The audited tree changed after them, so they
are stale and are not signed as current authority. All three raw transcripts are committed
unedited under `proof/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001/review_bundle/`;
the failing round is published, not discarded.

## Audit topology — named, not conflated

An audit cannot audit its own output, so the three heads are distinct:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` | exact substantive tree sent to AGY | `d2d3ff808e80e6d6a490616d4ff2341a63c29d86` |
| `AUDIT_EVIDENCE_HEAD` | successor adding only the report, raw transcript, defect reproduction, runner evidence | `9b901093e441a709d8c31e1067d5745a1604112f` |
| `SIGNED_PROOF_HEAD` | successor adding only the signed proof artefacts | the PR head |

`head_sha` in `PROOF.json` is the `AUDIT_EVIDENCE_HEAD`. Its delta from the audited tree is
only the audit's own outputs. The ordering is forced, because the trusted schema requires
`report_path` under a single `proof/` directory while proof-only closure confines the
successor commit to `proof/pr_merge/embedded-audit/pr-1165/`. Verify with:

```
git diff --name-only d2d3ff808e80e6d6a490616d4ff2341a63c29d86..9b901093e441a709d8c31e1067d5745a1604112f
```

No schema, validator, test, packet, documentation, or workflow byte changed after the audit.

## What this cycle repaired, and what it did not

**Repaired.** `scripts/audit/local_audit_acceptance.py` previously validated a signed
`embedded_audit` with a hand-rolled stdlib check that never walked `allOf` and exempted
`report_path`. A proof declaring `auditor_model: gemini-3.1-pro-high` with
`auditor_tool: claude-code-cli` — forbidden by this PR's own schema conditional — was
accepted. Reproduced before repair and recorded in
`review_bundle/DEFECT_REPRODUCTION_ROUND3.txt`. Both validation routes now execute the
canonical schema under real Draft 7 semantics and agree.

**Not repaired, and not claimed to be.** The separate scope gap over `proof/pr_merge/**` —
`proof/.validator_scope.json` skipping it under `skip_with_warning`, and the pre-commit
proof hook's `files` regex missing it — remains open. It is filed as
`TP-DMX-EMBEDDED-AUDIT-VALIDATOR-SCOPE-PARITY-001`. This proof is therefore validated by a
**direct** `scripts/audit/validate_audit_proof.py` run, which is the controlling result; the
`--all proof` sweep is not cited as evidence for it.

## Producer-invoked signing — explicit operator authorization

Standing rule **REVIEW-001** states that the producing agent must not author the signed
attestation for its own work. The operator issued a fresh, explicitly scoped override on
2026-08-10 for **this replacement proof only**, superseding the earlier proof-specific
authorization, which was consumed:

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1165 only
- authorized audited head: `9b901093e441a709d8c31e1067d5745a1604112f` only
- expires immediately after this proof is signed; no standing signing authority granted

Accordingly, and disclosed here rather than left implicit:

- The signing script was invoked by the **producer** (Claude Code), not by an independent
  party, using the operator's allow-listed key.
- The signature covers the newly generated `PROOF.json` byte-for-byte. The previous
  signature was not reused, and the proof was regenerated from the round-3 audit evidence
  rather than copy-edited.
- This override does **not** extend to any other packet, proof, or PR, and it does not
  weaken the signature-verification, allowed-signers, exact-head-binding, or
  proof-only-closure gates, none of which were modified.

A reviewer who considers producer-invoked signing insufficient for this change should treat
the AGY audit as the independent evidence and re-sign the identical bytes themselves; the
signature covers `PROOF.json` byte-for-byte, so re-signing requires no content change.
