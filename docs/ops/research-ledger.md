---
id: ops-research-ledger
title: DevOps AutoPR Research Ledger
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Evidence ledger for MP-DMX-DEVOPS-AUTOPR-001 governance scaffolding.
---
# DevOps AutoPR Research Ledger

## Evidence Used

| Evidence | Label | Use |
| --- | --- | --- |
| `AGENTS.md` | OBSERVED | Repo lifecycle, task-packet, proof, and boundary authority. |
| `PROJECT.md` | OBSERVED | Project-level split authority model. |
| `ARCHITECTURE.md` | OBSERVED | Multi-system architecture and known drift. |
| `PM_PLANE.md` | OBSERVED | PM metadata/workflow/decision/progress split. |
| `SERVICE_CATALOG.md` | OBSERVED | Service tier and status labels. |
| `docs/03-reference/truth/truth-systems.md` | OBSERVED | System role evidence. |
| `docs/03-reference/truth/truth-canonicals.md` | OBSERVED | Canonical path and runtime recommendations. |
| `docs/03-reference/systems/system-boundaries.md` | OBSERVED | Authority boundaries and forbidden patterns. |
| `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | OBSERVED | Strict task-packet schema. |
| Local CLI help output | OBSERVED | Tool invocation constraints for `agy`, `claude`, and `gemini`. |

## Research Limits

No live GitHub PR state beyond local `gh auth status` is treated as current PR truth because authentication failed in this run. No external vendor documentation was required to create this governance slice.
