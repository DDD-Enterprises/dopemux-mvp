# Signing disclosure — PR #1165 local attestation (replacement proof, round 4)

This disclosure and the `PROOF.json` beside it **supersede** the signed proof published at
PR head `e2b06ffbd0640c69bbb478f65d48361557efc4ba`, which was generated from round-3
evidence. That proof was superseded when a reviewer found that the canonical-schema refactor
this PR had just landed silently dropped a non-schema acceptance gate — `embedded_audit.required`
must be `true`. The gate was restored, the tree was re-audited (round 4), and this proof was
**regenerated from the round-4 evidence** rather than copy-edited with new SHAs.

The superseded proof must not be cited as current authority.

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

The auditor ran read-only (`--mode plan`), in fresh single-turn sessions (`num_turns: 1`),
and did not execute repository code. Four rounds were run:

| Round | AUDITED_TREE | Verdict |
|---|---|---|
| 1 | `491e59a8686b50782aee5b1bc245eb9c36dd2fd2` | FAIL — three risks |
| 2 | `02c915d8006ca5cddba9247ba9bf440581be7257` | PASS — zero risks |
| 3 | `d2d3ff808e80e6d6a490616d4ff2341a63c29d86` | PASS — zero risks, 11/11 |
| 4 (controlling) | `ca3ff647f8bdfd3cc85f6a15b5404d12617708b7` | **PASS** — zero risks, 10/10 |

Rounds 1–3 are historical evidence only. The audited tree changed after each, so none is
signed as current authority. All four raw transcripts are committed unedited under
`proof/TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001/review_bundle/`; the failing round
is published, not discarded, and so is the round that passed over a live defect.

### An audit limitation, preserved rather than rewritten

Round 3 returned **PASS 11/11 with an empty risk list over a tree that still carried the
live `required` gate regression** — and it was asked about gate preservation directly (its
Q4) and answered PASS. It was wrong. `@chatgpt-codex-connector`, reviewing the pushed head,
found the defect. That historical PASS is recorded here as what it actually was and is not
restated as anything stronger.

A clean audit verdict is evidence, not proof. Replacing a validator is a change class where
enumerating the old behaviour check-by-check is worth more than any single verdict — which
is what round 4 was given, and how the enumeration table in the auditor report came to exist.

## Audit topology — named, not conflated

An audit cannot audit its own output, so the three heads are distinct:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` | exact substantive tree sent to AGY in round 4 | `ca3ff647f8bdfd3cc85f6a15b5404d12617708b7` |
| `AUDIT_EVIDENCE_HEAD` | successor adding **only** the round-4 report, raw transcript and runner evidence | `06c4caa1763718239fabdb9d405fef6e2067b94d` |
| `SIGNED_PROOF_HEAD` | successor adding **only** the signed proof artefacts | the PR head |

`head_sha` in `PROOF.json` is the `AUDIT_EVIDENCE_HEAD`. Its delta from the audited tree is
only the audit's own outputs. The ordering is forced, because the trusted schema requires
`report_path` under a single `proof/` directory while proof-only closure confines the
successor commit to `proof/pr_merge/embedded-audit/pr-1165/`. Verify with:

```
git diff --name-only ca3ff647f8bdfd3cc85f6a15b5404d12617708b7..06c4caa1763718239fabdb9d405fef6e2067b94d
```

No schema, validator, test, packet, documentation, or workflow byte changed after the audit.
**AGY did not audit its own report.**

## What this cycle repaired, and what it did not

**Repaired — the `required` gate, as acceptance policy.** The pre-refactor hand-rolled
validator enforced `embedded_audit.required is True`. The canonical schema types `required`
as a plain boolean, so `{required: false, status: PASS}` is schema-**valid**; replacing the
structural check with Draft 7 execution removed the gate with no schema error to signal it.
It was not cosmetic: `build_embedded_audit_proof` promotes an accepted attestation to
`executed: true`, and `enforce_independent_audit_proof` checks the verdict and not this flag
— so the mandatory embedded-audit gate went **green** for a proof declaring the audit was
not required.

The distinction is deliberate and must stay explicit:

```
CANONICAL SCHEMA VALIDITY  +  LOCAL ATTESTATION POLICY  =  ACCEPTANCE
```

`required: true` is **acceptance policy**, enforced in `policy_errors()`. It is **not** a
schema rule, and the schema must keep admitting `required: false` because it also describes
CI-emitted diagnostic proofs. `POLICY_ONLY_REJECTIONS` in
`tests/audit/test_local_audit_acceptance.py` pins every fixture the schema accepts and
acceptance must reject — each asserted schema-valid first, so only policy can be the
rejecting authority. `test_rejects_required_false_even_though_schema_allows_it` is the
end-to-end regression.

**Also repaired, in round 3 and re-confirmed intact by round 4.**
`scripts/audit/local_audit_acceptance.py` previously validated a signed `embedded_audit`
with a hand-rolled stdlib check that never walked `allOf` and exempted `report_path`. A
proof declaring `auditor_model: gemini-3.1-pro-high` with `auditor_tool: claude-code-cli` —
forbidden by this PR's own schema conditional — was accepted. Reproduced before repair and
recorded in `review_bundle/DEFECT_REPRODUCTION_ROUND3.txt`. Both validation routes now
execute the canonical schema under real Draft 7 semantics and agree.

**Not repaired, and not claimed to be — two separate open defects.**

1. **Validator scope parity.** `proof/.validator_scope.json` skips `proof/pr_merge/**` under
   `skip_with_warning`, and the pre-commit proof hook has the same blind spot via
   `files ^proof/[^/]+/PROOF\.json$`. This proof is therefore validated by a **direct**
   `scripts/audit/validate_audit_proof.py` run, which is the controlling result; the
   `--all proof` sweep is not cited as evidence for it.
2. **Signing wrapper false success.** `scripts/audit/sign_local_audit_proof.sh` can print
   `signed: <path>.sig` when **no new signature was created**: with a stale `.sig` present,
   `ssh-keygen` prompts before overwriting, EOF declines the prompt, the old signature
   survives untouched, and the wrapper still reports apparent success. Wrapper stdout is not
   evidence of signing.

Both are filed as follow-ups and are deliberately **not** widened into this PR.

## How this signature was actually produced

Because of defect (2) above, the procedure did not trust the wrapper:

1. the stale `PROOF.json.sig` was **removed** from the working tree before signing, so a
   silent reuse of the superseded signature was not possible;
2. the signer was invoked over the newly generated `PROOF.json`;
3. the result was **independently verified** with `ssh-keygen -Y verify` against
   `config/audit/embedded-audit-allowed-signers` — principal `hue@local`, namespace
   `dopemux-embedded-audit`, exit `0` — not by reading wrapper stdout;
4. the new signature bytes were confirmed to **differ** from the superseded ones.

## Producer-invoked signing — explicit operator authorization

Standing rule **REVIEW-001** states that the producing agent must not author the signed
attestation for its own work. The operator issued a fresh, explicitly scoped override on
2026-08-10 for **this replacement proof only**, superseding all previously consumed PR #1165
signing authorizations:

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1165 only
- authorized audit lineage: `AUDITED_TREE ca3ff647f8bdfd3cc85f6a15b5404d12617708b7`,
  `AUDIT_EVIDENCE_HEAD 06c4caa1763718239fabdb9d405fef6e2067b94d`
- expires immediately after one valid replacement signature is produced; no standing signing
  authority granted

Accordingly, and disclosed here rather than left implicit:

- The signing script was invoked by the **producer** (Claude Code), not by an independent
  party, using the operator's allow-listed key.
- The signature covers the newly generated `PROOF.json` byte-for-byte. The previous
  signature was not reused, and the proof was regenerated from the round-4 audit evidence
  rather than copy-edited.
- This override does **not** extend to any other packet, proof, or PR, and it does not
  weaken the signature-verification, allowed-signers, exact-head-binding, or
  proof-only-closure gates, none of which were modified.

A reviewer who considers producer-invoked signing insufficient for this change should treat
the AGY audit as the independent evidence and re-sign the identical bytes themselves; the
signature covers `PROOF.json` byte-for-byte, so re-signing requires no content change.
