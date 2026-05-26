---
id: ops-config-registry
title: DevOps AutoPR Config Registry
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Registry of governance artifacts introduced by MP-DMX-DEVOPS-AUTOPR-001.
---
# DevOps AutoPR Config Registry

## Artifact Registry

| Artifact | Path | Authority |
| --- | --- | --- |
| Embedded audit schema | `schemas/proof/embedded_audit.schema.json` | Defines proof object shape only. |
| Merge readiness schema | `schemas/pr_steward/merge_readiness.schema.json` | Defines check-only readiness envelope. |
| Review item ledger schema | `schemas/pr_steward/review_item_ledger.schema.json` | Defines review item classification records. |
| Thread dispositions schema | `schemas/pr_steward/thread_dispositions.schema.json` | Defines review-thread disposition records. |
| CI triage schema | `schemas/pr_steward/ci_triage.schema.json` | Defines status-check triage records. |
| Macro packet record | `task-packets/generated/MP-DMX-DEVOPS-AUTOPR-001.json` | Current governance slice packet. |
| PR Steward packet record | `task-packets/generated/TP-DMX-PR-STEWARD-001.json` | Future check-only implementation packet. |
| Proof bundle | `proof/MP-DMX-DEVOPS-AUTOPR-001/PROOF.json` | Current execution proof. |
| Auditor report | `proof/MP-DMX-DEVOPS-AUTOPR-001/AUDITOR_REPORT.md` | Embedded audit output or skipped-audit evidence. |

## Secret Policy

This registry stores no secrets, tokens, credentials, provider keys, or private account metadata. Prompt files must require operators to reference secret locations indirectly and must never ask implementers to paste secrets into proof.

## Drift Handling

When a local tool version, GitHub authentication state, schema, or repo authority changes, update the proof for the current packet. Update this registry only when the artifact contract changes.
