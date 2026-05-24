---
id: fast-dev-os-proof-ledger
title: Fast Dev OS — Proof Ledger (Snapshot)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Snapshot of `proof/**/PROOF.json` artifacts at the time this ledger was authored. Verdicts are advisory; live `python -m json.tool proof/.../PROOF.json` for current truth.
---
# Fast Dev OS — Proof Ledger

> **⚠️ SNAPSHOT — NOT LIVE TRUTH.** Run `find proof -name "PROOF.json" -type f | sort` for live state.

## Relationship to governance

This snapshot **operationalizes** [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md) (which defines proof rules) and [`AGENTS.md §9`](../../../AGENTS.md) (which defines required proof fields). It **does not override** either source. When this snapshot and a live PROOF.json conflict, the live file wins.

## AGENTS.md §9 required proof fields (reminder)

Every PROOF.json for repo-changing work must include:

- TP path / ID
- Worktree path
- Branch
- Repo identity result
- Slices completed
- Files changed
- Validations with exit codes
- Codereview status
- Precommit status
- Commit SHA
- PR URL or exact blocker
- Residual risks
- UNKNOWNs
- Cleanup status

**No proof means incomplete.** Final confidence must be `VERIFIED`.

## Snapshot metadata

```yaml
snapshot:
  taken_at: '2026-05-23T02:33:00Z'
  repo_head: 8e7a2283f56a49abfb41c2ac791cbf18dd0ae500
  ledger_class: snapshot
  refresh_policy: manual-per-session
  refresh_command: 'find proof -name "PROOF.json" -type f | sort'
  taken_by: 'TP-DMX-FDOS-004-AUTHORITY-REFRESH (initial authoring)'
```

## Proof artifacts at snapshot time (~25 total)

| PROOF.json path | Status field |
|-----------------|--------------|
| `proof/TP-CODEX-RTE-V5-BOUNDED-APPLY-20260402/PROOF.json` | (no `status`/`verdict`/`validation_state` field — needs schema check) |
| `proof/TP-CODEX-RTE-V5-BRANCH-HYGIENE-AND-COMMIT-ISOLATION-20260402/PROOF.json` | (no normalized status) |
| `proof/TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401/PROOF.json` | (no normalized status) |
| `proof/TP-CODEX-RTE-V5-OFFLINE-HARDENING-AND-TRUST-CLEANUP-20260402/PROOF.json` | (no normalized status) |
| `proof/TP-CODEX-RTE-V5-PROOF-TO-RUNTIME-RECONCILIATION-20260402/PROOF.json` | (no normalized status) |
| `proof/TP-DMX-RTE-55PRO-AUDIT-ASSEMBLY-001/PROOF.json` | (no normalized status) |
| `proof/TP-OPS-MAC-SCRUBBER-001/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-BATCH-005/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-BATCH-E2E-006/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-DOCS-CANON-008/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-STRICT-ATTESTATION-007/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-V3-CONSENT-004/PROOF.json` | (no normalized status) |
| `proof/TP-RTE-WALKER-006/PROOF.json` | (no normalized status) |
| `proof/codex-refresh/TP-DMX-CODEX-REFRESH-001-AUTHORITY-MATRIX/PROOF.json` | (no normalized status) |
| `proof/codex-refresh/TP-DMX-CODEX-REFRESH-002-OPERATOR-RUNBOOK/PROOF.json` | (no normalized status) |
| `proof/repo-truth-extractor/TP-CODEX-RTE-MAIN-PR-001/PROOF.json` | `PASS` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-MERGE-EXEC-001/PROOF.json` | `PASS` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-PR-REVIEW-001/PROOF.json` | `PASS` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-001/PROOF.json` | `LOCAL_PASS_WITH_ENVIRONMENT_NO_GO` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-001A/PROOF.json` | `PASS` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-005/PROOF.json` | `PASS` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-PRELIVE-007/PROOF.json` | `FAIL` |
| `proof/repo-truth-extractor/TP-CODEX-RTE-RECOVERY-UNCOMMITTED-001/PROOF.json` | `PARTIAL` |
| `proof/rte-ux/RTE-UX-PKT-AUTHORITY-ORDER-RECONCILIATION-001/PROOF.json` | (no normalized status) |
| `proof/rte-ux/RTE-UX-PKT-CLAUDE-RTE-SAFETY-GUIDANCE-001/PROOF.json` | (no normalized status) |
| `proof/rte-ux/RTE-UX-PKT-CLI-TONE-EMOJI-CLEANUP-001/PROOF.json` | (no normalized status) |

## Status field heterogeneity (OBSERVED, not yet resolved)

Many existing PROOF.json files lack a normalized top-level `status` / `verdict` / `validation_state` field. The `repo-truth-extractor/` series uses `status: PASS|FAIL|PARTIAL|LOCAL_PASS_WITH_ENVIRONMENT_NO_GO` consistently. Other series use ad-hoc structures.

**This is an OBSERVED CONFLICTING state**, not a Fast Dev OS layer responsibility to fix. The proper resolution is `TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES` (the third packet in this series), which will define a canonical PROOF_BUNDLE_TEMPLATE.json and a `verdict` field standard. Until then, treat existing PROOF.json files individually.

## Cross-reference: chat-context-v2

The chat-context-v2 corpus at `$HOME/Downloads/dopemux-chat-context-v2/04_reconciled/PR_PACKET_PROOF_MAP.md` cross-references PROOF citations with the PR/TP graph. See [`evidence-notes.md`](evidence-notes.md) for provenance.

## Truth posture

Statuses cited here are read from each PROOF.json's `status` field at snapshot time. Files with no `status`/`verdict`/`validation_state` field are not guaranteed PASS/FAIL — they may have richer per-field validation records. Always read each PROOF.json in full before treating it as authoritative for any TP's acceptance.
