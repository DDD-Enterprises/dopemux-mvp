# Signing disclosure — PR #1165 local attestation (replacement proof)

This disclosure supersedes the one published with the previous signed proof, which was
orphaned when the branch was rebased onto `5d694cc989` and repaired.

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
execute repository code. Two rounds were run against
`491e59a8686b50782aee5b1bc245eb9c36dd2fd2` (verdict FAIL, three risks) and
`02c915d8006ca5cddba9247ba9bf440581be7257` (verdict PASS, zero risks). Both raw transcripts
are committed unedited under
`proof/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001/review_bundle/`; the failing round
is published, not discarded.

## What the audited head contains that the auditor did not see

`head_sha` in `PROOF.json` is `4d6cc9a1f673e58ad47f7af5e5aabe498646dfd4`, which sits one
commit above the tree AGY reviewed. That delta is only the audit's own outputs — the
canonical report and the raw transcripts and runner-evidence captures. The ordering is
forced, because the trusted schema requires `report_path` under a single `proof/` directory
while proof-only closure confines the successor commit to
`proof/pr_merge/embedded-audit/pr-1165/`. Verify with:

```
git diff --name-only 02c915d8006ca5cddba9247ba9bf440581be7257..4d6cc9a1f673e58ad47f7af5e5aabe498646dfd4
```

No schema, test, packet, documentation, or workflow byte changed after the audit.

## Producer-invoked signing — explicit operator authorization

Standing rule **REVIEW-001** states that the producing agent must not author the signed
attestation for its own work. The operator issued a fresh, explicitly scoped override on
2026-08-10 for **this replacement proof only**, superseding the earlier proof-specific
authorization:

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1165 only
- authorized audited head: `4d6cc9a1f673e58ad47f7af5e5aabe498646dfd4` only
- expires immediately after this proof is signed; no standing signing authority granted

Accordingly, and disclosed here rather than left implicit:

- The signing script was invoked by the **producer** (Claude Code), not by an independent
  party, using the operator's allow-listed key.
- The signature covers the newly generated `PROOF.json` byte-for-byte. The previous
  signature was not reused, and the previous proof was regenerated from the new audit
  evidence rather than copy-edited.
- This override does **not** extend to any other packet, proof, or PR, and it does not
  weaken the signature-verification, allowed-signers, exact-head-binding, or
  proof-only-closure gates, none of which were modified.

A reviewer who considers producer-invoked signing insufficient for this change should treat
the AGY audit as the independent evidence and re-sign the identical bytes themselves; the
signature covers `PROOF.json` byte-for-byte, so re-signing requires no content change.
