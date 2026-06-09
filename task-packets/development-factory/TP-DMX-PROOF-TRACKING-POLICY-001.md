---
id: TP-DMX-PROOF-TRACKING-POLICY-001
title: Proof Bundle Git-Tracking Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
status: READY_FOR_REVIEW
prelude: Formalizes the default-track rule for sanitized proof bundles. Corrects the prior default-ignore posture that caused TP-DMX-DDF-DOCS-001 proof to be silently dropped.
---
# Task Packet: TP-DMX-PROOF-TRACKING-POLICY-001 · Development Factory · Proof Bundle Git-Tracking Policy

════════════════════════════════════════════════════════════

## Objective

Establish and document the rule: **proof bundles are tracked by default**. Update the `.gitignore` proof exclusions, the proof governance docs, and the `evidence-and-proof-flow.md` DDF reference to reflect this. Create or update the canonical proof-directory rules to include the git-tracking tier.

────────────────────────────────────────────────────────────

## Why This Packet Exists Now

`TP-DMX-DDF-DOCS-001` created `proof/TP-DMX-DDF-DOCS-001/PROOF.json` and `SUMMARY.md` but they were silently gitignored by `.gitignore:362` (`proof/*`). The docs were committed; the proof that validates them was not. This breaks the auditability invariant: a governed factory run with no tracked proof is a governed factory run that can't be replayed or reviewed.

`TP-DMX-DDF-DOCS-CORRECT-001` demonstrated the correct behavior: use `git add -f` to force-track sanitized proof files while leaving the blanket `proof/*` ignore in place as a safety net for raw artifacts.

This packet codifies the rule so future agents and operators don't repeat the default-ignore mistake.

────────────────────────────────────────────────────────────

## Policy

### Default: Track Sanitized Proof

The following proof artifact types **MUST be committed**:

| Artifact | File Pattern | Notes |
|----------|-------------|-------|
| Proof bundle | `PROOF.json` | Machine-readable; always track |
| Proof summary | `SUMMARY.md` | Human-readable; always track |
| Audit record | `AUDIT.md` | When produced by AI review |
| Merge readiness | `MERGE_READINESS.json` | When produced by PR Steward |
| Validation summary | `VALIDATION.md` | Summarized gate results |
| Command-output summary | `CMD_SUMMARY.md` | Sanitized command outputs (not raw stdout) |
| Model-routing receipt | `MODEL_ROUTING.json` | Which model ran which stage |
| Proof manifest | `MANIFEST.json` | Index of what's in the bundle |

### Exception: Do NOT Track

| Artifact | Reason |
|----------|--------|
| Raw stdout/stderr dumps > 50 KB | Bloats repo history; low signal density |
| Telemetry / metrics logs | Ephemeral runtime data |
| `.env` contents or any secret-containing output | Security |
| API responses that include tokens or credentials | Security |
| Generated artifacts > 1 MB (binaries, embeddings, etc.) | Repo size |
| Cache files | Regenerable |
| Screenshots unless sanitized and < 500 KB | Usually ephemeral |
| Raw LLM transcripts (full multi-turn JSON) | Use SUMMARY.md instead |

### Gitignore Strategy

The blanket `proof/*` rule in `.gitignore` remains as a **safety net** — it prevents raw artifacts from being accidentally staged. When adding sanitized proof files, use `git add -f <path>` explicitly. This forces the operator to make a conscious decision about what to track.

Do NOT replace `proof/*` with granular ignore patterns. The force-add approach is preferable because:
1. It keeps dangerous defaults in place (secrets / giant files stay out by default).
2. It makes proof tracking an explicit, auditable action per commit.
3. It works with any proof file layout without requiring `.gitignore` maintenance per packet.

────────────────────────────────────────────────────────────

## Scope

IN (modify existing docs + create packet):

* `docs/03-reference/development-factory/evidence-and-proof-flow.md` — add "Git Tracking" section
* `docs/03-reference/governance/proof-directory-rules.md` — add tracking tier table
* `docs/03-reference/governance/proof-path-normalization-rules.md` — add note on force-add convention
* `docs/03-reference/development-factory/red-lines-and-stop-conditions.md` — add red line: "Proof not committed after packet completion"
* `task-packets/development-factory/TP-DMX-PROOF-TRACKING-POLICY-001.md` (this file)

OUT (do not touch):

* `.gitignore` — the `proof/*` rule stays; no changes
* Runtime code, schemas, `config/`, `.github/workflows/`
* ConPort / dope-memory / dope-context state
* `queue_drain.py`, `scripts/batch_resolve_and_merge.py`
* Any proof files already committed or gitignored

────────────────────────────────────────────────────────────

## Invariants

* Docs-only packet. No runtime code, schema, or config touched.
* `.gitignore` is NOT modified — the blanket `proof/*` ignore is preserved as a safety net.
* No secrets are printed or committed.
* The policy is additive — it does not retroactively require re-committing proof for past packets. Past proof remains on disk as `NOT_COMMITTED` where applicable.

────────────────────────────────────────────────────────────

## Exact Commands to Run

```bash
# Verify .gitignore proof rule exists and note line number
grep -n "proof" .gitignore

# After doc edits, confirm no forbidden paths touched
git status --porcelain | rg "queue_drain|batch_resolve|schemas/development-factory|config/ai|src/"

# Verify PROOF.json is valid
python -m json.tool proof/TP-DMX-PROOF-TRACKING-POLICY-001/PROOF.json
```

────────────────────────────────────────────────────────────

## Acceptance Criteria

* `evidence-and-proof-flow.md` documents the default-track rule and the force-add convention.
* `proof-directory-rules.md` includes a tracking tier table (TRACK / DO_NOT_TRACK with file patterns).
* `proof-path-normalization-rules.md` includes a note on `git add -f`.
* `red-lines-and-stop-conditions.md` includes: "Proof bundle not committed for a completed packet" as a stop condition.
* The `.gitignore` `proof/*` rule is unchanged.
* No runtime code, schema, or config is touched.
* Packet exists; proof JSON exists and validates.

────────────────────────────────────────────────────────────

## Rollback

* `git checkout -- docs/03-reference/development-factory/evidence-and-proof-flow.md docs/03-reference/governance/proof-directory-rules.md docs/03-reference/governance/proof-path-normalization-rules.md docs/03-reference/development-factory/red-lines-and-stop-conditions.md`
* `rm -rf task-packets/development-factory/TP-DMX-PROOF-TRACKING-POLICY-001.md proof/TP-DMX-PROOF-TRACKING-POLICY-001/`

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop immediately if: a correction requires runtime code / schema / config changes, `.gitignore` modification that weakens the `proof/*` safety net, secret exposure, or scope escape into ConPort / dope-memory / dope-context writes. If stopped, return attempted steps, evidence collected, exact blocker, recommended next action.

## Next Recommended Packet

`TP-RTE-S7-DRIFT-FIX-001` (re-scoped to verify-and-close: run the S7 gate against injected drift, confirm FAIL).
