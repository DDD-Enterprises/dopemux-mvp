# Signing disclosure — PR #1223 local attestation (canonical embedded-audit bridge)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-TRUST-GATE-FAIL-CLOSED-001` / PR #1223, after the hosted PAL/Claude
embedded-audit run failed with `Credit balance is too low` and the workflow's
trusted local fallback found no canonical signed attestation on record.

## What this bridge is, and is not

This is **not** a new repair, a new audit, or a re-audit of the substantive
code. It is a proof-only publication step that lets the trusted embedded-audit
CI gate accept evidence this packet already produced. Three heads are in play,
named rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (C1) | frozen substantive content, examined by both audits below | `352a3d888d1ce5116b9af65d696fe62373728a7c` |
| `AUDIT_EVIDENCE_HEAD` (C3) | proof-only successor adding both audit reports/transcripts | `ab4d2ae6b155b13f331dc2cfdd5112a943aea402` |
| `SIGNED_PROOF_HEAD` (this bridge, C4) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1223/**` | the PR head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (C3). Its delta from C1 is
proof-only (`proof/TP-DMX-TRUST-GATE-FAIL-CLOSED-001/**` exclusively); no
substantive byte changed after C1. Verify with:

```
git diff --name-only 352a3d888d1ce5116b9af65d696fe62373728a7c..ab4d2ae6b155b13f331dc2cfdd5112a943aea402
```

## Independence of the two audits already on record

Two audits were already produced for this packet, before this bridge existed:

| Pass | Runner | Model | Independence | Verdict |
|---|---|---|---|---|
| 1 (supporting, schema-representable) | Claude Code `quality-engineer` subagent | Sonnet 5 | `LIMITED` — same runtime/company family as the implementer, ruled by supervisor disposition 2026-08-12 | `PASS_WITH_RISKS` |
| 2 (**controlling**, not schema-representable) | CommandCode CLI v1.17.0 | `gpt-5.3-codex` (evidence-gathering) then `deepseek/deepseek-v4-flash` (continuation, unintended session-resume fallback, disclosed) | `PROVEN_AGAINST_IMPLEMENTER` — genuinely distinct tool and model vendors from both the implementer and the pass-1 auditor | `PASS_WITH_RISKS` |

The schema-bound `embedded_audit` object in `PROOF.json` truthfully describes
**pass 1 only**: `auditor_tool: claude-code-cli`, `auditor_model: sonnet`.
`schemas/proof/embedded_audit.schema.json`'s enums have no slot for
CommandCode, GPT-5.3-Codex, or DeepSeek — and `schemas/**` is outside this
packet's file allowlist, so the enum cannot be extended here. Rather than
falsely representing CommandCode as `pal-mcp-clink` or DeepSeek as `sonnet`,
the schema-bound object stays literally true and the controlling pass-2 audit
is carried in full in `embedded_audit.remaining_risks` (free text, outside the
schema's tool/model constraint) with an explicit pointer to
`proof/TP-DMX-TRUST-GATE-FAIL-CLOSED-001/AUDITOR_REPAIR_REPORT.md`.

**This bridge does not weaken or replace that governance.** Pass 1 remains
`LIMITED` supporting evidence. Pass 2 (CommandCode) remains the controlling L3
audit for this packet's readiness. This bridge exists solely to satisfy CI's
mechanical requirement for a schema-conformant, signed `embedded_audit` object
so the `embedded-audit` and `PR Steward` workflows can execute at all.

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for
its own work without an explicit, narrowly-scoped operator override (see the
PR #1165 precedent, `proof/pr_merge/embedded-audit/pr-1165/SIGNING_DISCLOSURE.md`).
The operator granted a fresh override for this bridge commit only, via an
`AskUserQuestion` confirmation in-session (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1223 only
- authorized audit lineage: `AUDITED_TREE 352a3d888d1ce5116b9af65d696fe62373728a7c`,
  `AUDIT_EVIDENCE_HEAD ab4d2ae6b155b13f331dc2cfdd5112a943aea402`
- expires immediately after one valid signature is produced; no standing
  signing authority granted

Accordingly:

- The signing script was invoked by the **producer** (Claude Code, this
  session), not by an independent party, using the operator's allow-listed key
  already provisioned on this machine.
- The signature covers this `PROOF.json` byte-for-byte.
- This override does **not** extend to any other packet, proof, or PR, and it
  does not weaken the signature-verification, allowed-signers,
  exact-head-binding, or proof-only-closure gates in
  `scripts/audit/local_audit_acceptance.py`, none of which were modified.

## How this signature was actually produced

Per the known signing-wrapper false-success defect (documented in the PR #1165
precedent — `scripts/audit/sign_local_audit_proof.sh` can print `signed:
<path>.sig` when no new signature was actually created, if a stale `.sig`
already exists and `ssh-keygen` declines an overwrite prompt on EOF), the
procedure does not trust wrapper stdout alone:

1. any pre-existing `PROOF.json.sig` at this path is removed before signing;
2. the signer is invoked over this exact, already schema-validated
   `PROOF.json`;
3. the result is **independently verified** with `ssh-keygen -Y verify`
   against `config/audit/embedded-audit-allowed-signers` (principal
   `hue@local`, namespace `dopemux-embedded-audit`), not by reading wrapper
   stdout;
4. `scripts/audit/local_audit_acceptance.py` is run locally against the
   prospective successor head before commit, and `accepted=true` is required.

## What this bridge explicitly does not authorize

No mark-ready. No merge. No force push. No history rewrite. No branch
deletion. No production mutation. No re-audit of C1. No substantive change —
this commit's diff versus C3 is confined to
`proof/pr_merge/embedded-audit/pr-1223/**`.
