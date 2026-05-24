---
id: fast-dev-os-template-acceptance-decision
title: Fast Dev OS — Acceptance Decision Template
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Standard shape for the operator's accept/reject/rework decision record. The acceptance decision is the authoritative end-of-cycle artifact for any Task Packet; it closes the loop on the Fast Dev OS execution lifecycle.
---
# Fast Dev OS — Acceptance Decision Template

## Relationship to governance

This template **operationalizes** [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md) and AGENTS.md §9 proof-and-finality contract; it **does not override** them.

## Lane

**L0–L6** — every TP, regardless of lane, ends with an acceptance decision.

## When to use

After receiving the implementer's report (and the auditor's findings, if lane ≥ L3). The operator is the authoritative decider. The acceptance decision becomes part of the TP's audit trail — append to PROOF.json's `remediation_log` (if rework) or `acceptance_decision` field (new field for this template).

## Template

```markdown
# Acceptance Decision — <TP-ID>

## Identity
- TP path: `<task-packets/generated/TP-*.json>`
- TP ID: `<TP-DMX-...>`
- PR URL: `<https://github.com/DDD-Enterprises/dopemux-mvp/pull/NNN>`
- Lane: `<L0|L1|L2|L3|L4|L5|L6>`
- Decision date (UTC): `<ISO timestamp>`
- Decided by: `<operator name>`

## Decision
**`<ACCEPT | ACCEPT_WITH_FOLLOWUP | REJECT_FOR_REWORK | REJECT_PERMANENTLY>`**

## Rationale (≥ 1 sentence required)
<Why this decision. Cite implementer report sections and audit findings.>

## Inputs reviewed
- Implementer report: `<path or PR comment URL>`
- PROOF.json: `<proof/<series>/TP-*/PROOF.json>`
- Audit findings (if L3+): `<path or PR comment URL>`
- Live `gh pr view <N>`: `<key state at decision time>`
- Live `git log --oneline origin/main..<branch>`: `<commits to be merged>`

## Decision matrix
| Criterion | Status | Notes |
|-----------|--------|-------|
| TP allowlist compliance | PASS / FAIL | `<N>` paths in allowlist; `<M>` actually changed |
| AGENTS.md §9 PROOF complete | PASS / FAIL | Missing fields: `<list if FAIL>` |
| NOT_RUN items justified | PASS / FAIL | Unjustified: `<list if FAIL>` |
| Codereview status | PASS / PARTIAL / FAIL | Verdict: `<...>` |
| Precommit status | PASS / FAIL | Verdict: `<...>` |
| Audit verdict (L3+) | PASS / PASS_WITH_NOTES / PARTIAL / FAIL / NOT_READY / NOT_REQUIRED | Lane: `<...>` |
| Residual risks acknowledged | PASS / FAIL | Risks: `<list>` |
| UNKNOWNs documented | PASS / FAIL | UNKNOWNs: `<count>` |
| Secrets / PII clean | PASS / FAIL | If FAIL, immediate remediation required |
| Truth posture honored | PASS / FAIL | No invented paths/commands/branches/PRs/tests/capabilities |

## Conditions (if ACCEPT_WITH_FOLLOWUP)
- `<followup TP-ID or issue number>`: `<what must happen by when>`

## Rework requested (if REJECT_FOR_REWORK)
- `<change required>`: `<rationale>`
- New implementer prompt to use: `<which prompt from this directory>`
- Lane (may change): `<L0|L1|L2|L3|L4|L5|L6>`
- Estimated rework scope: `<minimal | moderate | substantial>`

## Permanent rejection rationale (if REJECT_PERMANENTLY)
- Why this work cannot be salvaged: `<specific reasons>`
- Cleanup required: `<branch deletion, worktree removal, etc.>`
- Lessons learned for future TPs: `<one or two notes>`

## Merge authorization (if ACCEPT or ACCEPT_WITH_FOLLOWUP)
- Merge strategy: `<squash | merge commit | rebase>`
- Merge target: `<main>`
- Authorized by: `<operator name>`
- Merge command run: `<gh pr merge N --squash | manual>`
- Merge commit SHA: `<SHA>` (after merge)

## Post-merge actions
- Update PROOF.json `cleanup_status` to `WORKTREE_REMOVED` (after worktree cleanup)
- Update TP series ledger: `<TP-DMX-FDOS-NNN status MERGED>`
- Update `packet-ledger.md` if doing the next snapshot
- Update `pr-ledger.md` if doing the next snapshot
- Update `unknown-conflicting-stale.md` resolution_changelog if this packet resolved any UNRESOLVED items

## Truth posture (applies to acceptance decision)
> Never accept on faith. If audit found unresolved gaps, document them. If you accept anyway, document the residual risk explicitly.

> Final confidence requires VERIFIED. If you cannot mark VERIFIED, decide based on what you actually know — never on what you wish were true.
```

## Forbidden in acceptance decisions

- Accepting without an implementer report.
- Accepting work that has UNRESOLVED CRITICAL audit findings.
- Accepting work where PROOF.json is incomplete per AGENTS.md §9.
- Accepting and merging without explicit merge authorization line.
- Marking ACCEPT when fields in the decision matrix show FAIL without conditions.
- Hiding residual risks to make the decision look clean.

## After acceptance decision

- If ACCEPT or ACCEPT_WITH_FOLLOWUP: execute merge per the authorized strategy; update PROOF.json post-merge.
- If REJECT_FOR_REWORK: brief the new implementer with the requested rework + the prior outputs.
- If REJECT_PERMANENTLY: execute cleanup; capture lessons in the next snapshot ledger refresh.

## Truth posture for the operator

> You are the latest-user-instruction authority per AGENTS.md §2. You can override the auditor and the implementer, but you cannot override evidence. If the diff says X and the implementer says Y, X wins.

> Your acceptance decision is part of the audit trail. Write it as if a future maintainer (or auditor) will read it without context — because they will.
