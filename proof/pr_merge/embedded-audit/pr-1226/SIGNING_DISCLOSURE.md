# Signing disclosure — PR #1226 local attestation (canonical embedded-audit bridge)

This disclosure and the `PROOF.json` beside it satisfy the trusted, signed
local-attestation fallback (`scripts/audit/local_audit_acceptance.py`) for
`TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001` / PR #1226, after the hosted embedded-audit
run (`31563565050`) failed with `Credit balance is too low` (a provider-credit
failure mode, not a substantive finding — confirmed by downloading and inspecting
the run's raw artifact output) and the workflow's trusted local fallback found no
canonical signed attestation on record.

## What this bridge is, and is not

This is **not** a new repair, a new audit, or a re-audit of the substantive code.
It is a proof-only publication step that lets the trusted embedded-audit CI gate
accept evidence this packet already produced. Three heads are in play, named
rather than conflated:

| Term | Meaning | SHA |
|---|---|---|
| `AUDITED_TREE` (C1) | frozen substantive content, examined by the controlling Codex audit | `40783797fe30325766a2cb6f53aaa53254785712` |
| `AUDIT_EVIDENCE_HEAD` (C4) | proof-only successor adding the schema-repair (C3) and the supporting audit record (C4) | `1e45baf9430355b0debf0ad1735ba735d54c1f32` |
| `SIGNED_PROOF_HEAD` (this bridge, C5) | proof-only successor adding **only** `proof/pr_merge/embedded-audit/pr-1226/**` | the PR head after this commit |

`head_sha` in `PROOF.json` is `AUDIT_EVIDENCE_HEAD` (C4). Its delta from C1 is
proof-only (`proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/**` exclusively); no
substantive byte changed after C1. Verified with:

```
git diff --name-only 40783797fe30325766a2cb6f53aaa53254785712..1e45baf9430355b0debf0ad1735ba735d54c1f32 -- ':!proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/**'
# empty
git merge-base --is-ancestor 40783797fe30325766a2cb6f53aaa53254785712 1e45baf9430355b0debf0ad1735ba735d54c1f32
# C1 is an ancestor of C4
```

## Independence of the two audits already on record

Two audits exist for this packet, both predating this bridge:

| Pass | Runner | Model | Independence | Verdict |
|---|---|---|---|---|
| Supporting, schema-representable (C4) | Claude Code `quality-engineer` subagent | Sonnet 5 | `LIMITED` — same runtime/company family as the implementer | `PASS` |
| **Controlling**, not schema-representable (bound to C1) | Codex CLI, via `codex:codex-rescue` | OpenAI GPT-5 Codex, ChatGPT/Codex API runtime | `OBSERVED` — genuinely distinct tool and model vendor from the implementer | `PASS_WITH_RISKS` (two passes: pass 1 NEEDS_SUPERVISOR → repair → pass 2 controlling PASS_WITH_RISKS, all risks non-blocking) |

The schema-bound `embedded_audit` object in `PROOF.json` truthfully describes the
supporting audit only: `auditor_tool: claude-code-cli`, `auditor_model: sonnet`.
`schemas/proof/embedded_audit.schema.json`'s enums have no slot for Codex/GPT-5
Codex — and `schemas/**` is outside this packet's file allowlist, so the enum
cannot be extended here. Rather than falsely representing Codex as
`pal-mcp-clink` or `gemini`, the schema-bound object stays literally true and the
controlling audit is carried in full in `embedded_audit.remaining_risks` (free
text, outside the schema's tool/model constraint) with an explicit pointer to
`proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/AUDITOR_REPORT.md`.

**This bridge does not weaken or replace that governance.** The supporting audit
remains `LIMITED`. The Codex audit remains the controlling L3 audit for this
packet's readiness, bound to C1. This bridge exists solely to satisfy CI's
mechanical requirement for a schema-conformant, signed `embedded_audit` object so
the `embedded-audit` and `PR Steward` workflows can execute at all. This follows
the PR #1223 precedent pattern exactly
(`proof/pr_merge/embedded-audit/pr-1223/SIGNING_DISCLOSURE.md`).

## Producer-invoked signing — explicit, scoped operator override

Standing rule: the producing agent must not author the signed attestation for its
own work without an explicit, narrowly-scoped operator override (PR #1165
precedent). The operator granted a fresh, in-session override for this bridge
commit only, via an `AskUserQuestion` confirmation (recommended option selected):

- authorized principal: `hue@local`
- authorized namespace: `dopemux-embedded-audit`
- authorized target: PR #1226 only
- authorized audit lineage: `AUDITED_TREE 40783797fe30325766a2cb6f53aaa53254785712`,
  `AUDIT_EVIDENCE_HEAD 1e45baf9430355b0debf0ad1735ba735d54c1f32`
- expires immediately after one valid signature is produced; no standing signing
  authority granted

Accordingly:

- The signing script was invoked by the **producer** (Claude Code, this session),
  not by an independent party, using the operator's allow-listed key already
  provisioned on this machine (`~/.ssh/dopemux_audit_signing`).
- The signature covers this `PROOF.json` byte-for-byte.
- This override does **not** extend to any other packet, proof, or PR, and it
  does not weaken the signature-verification, allowed-signers, exact-head-binding,
  or proof-only-closure gates in `scripts/audit/local_audit_acceptance.py`, none
  of which were modified.

## How this signature was actually produced

Per the known signing-wrapper false-success defect (`scripts/audit/sign_local_audit_proof.sh`
can print `signed: <path>.sig` when no new signature was actually created, if a
stale `.sig` already exists and `ssh-keygen` declines an overwrite prompt on
EOF), the procedure does not trust wrapper stdout alone:

1. any pre-existing `PROOF.json.sig` at this path is removed before signing (none
   existed — first signature for this PR);
2. the signer is invoked directly with `ssh-keygen -Y sign` over this exact,
   already schema-validated `PROOF.json` (bypassing the wrapper script);
3. the result is **independently verified** with `ssh-keygen -Y verify` against
   `config/audit/embedded-audit-allowed-signers` (principal `hue@local`, namespace
   `dopemux-embedded-audit`), not by reading wrapper stdout;
4. `scripts/audit/local_audit_acceptance.py` is run locally against the
   prospective successor head before commit, and `accepted=true` is required.

## What this bridge explicitly does not authorize

No mark-ready. No merge. No force push. No history rewrite. No branch deletion.
No production mutation. No re-audit of C1. No substantive change — this commit's
diff versus C4 is confined to `proof/pr_merge/embedded-audit/pr-1226/**`.
