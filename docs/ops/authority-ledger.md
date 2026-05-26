---
id: ops-authority-ledger
title: DevOps AutoPR Authority Ledger
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Claim-labeled authority ledger for the governance-first AutoPR workflow slice.
---
# DevOps AutoPR Authority Ledger

## Claim Labels

- OBSERVED: directly supported by local files, commands, schemas, or runtime code.
- INFERRED: derived from multiple observed signals.
- PROPOSED: introduced by this governance slice and not yet implemented as runtime.
- UNKNOWN: unresolved by this slice.
- CONFLICTING: sources disagree and the conflict is preserved.
- CLAIMED: present in prose without enough runtime evidence to treat as observed.

## Ledger

| Domain | Authority | Label | Evidence / Boundary |
| --- | --- | --- | --- |
| Repo execution control | Active task packet and AGENTS.md lifecycle | OBSERVED | `AGENTS.md` and `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`. |
| Runtime behavior claims | Code, config, compose, tests, active entrypoints | OBSERVED | Repo truth order in `AGENTS.md`, `PROJECT.md`, and `ARCHITECTURE.md`. |
| Task-packet schema | `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | OBSERVED | Root-level `dopetask-cannonical-spec.json` is absent in this checkout. |
| Operator CLI/control | `dopemux` | OBSERVED | `PROJECT.md`, `ARCHITECTURE.md`, and truth docs. |
| Execution runtime | external `dopetask` through `scripts/dopetask` | OBSERVED | `PROJECT.md`, `ARCHITECTURE.md`, and `docs/03-reference/truth/truth-canonicals.md`. |
| PM metadata | Leantime | OBSERVED | `PM_PLANE.md` maps passive metadata and snapshots to Leantime. |
| Workflow transitions/views | task-orchestrator | OBSERVED | `PM_PLANE.md` and task-orchestrator reference docs. |
| Decisions/progress/context | ConPort | OBSERVED | `PM_PLANE.md` and system boundaries. |
| Historical receipts | dope-memory | OBSERVED | `PM_PLANE.md` and `docs/03-reference/truth/truth-systems.md`. |
| Retrieval | dope-context plus ConPort | OBSERVED | `SYSTEM_BOUNDARIES.md` and `docs/03-reference/truth/truth-interfaces.md` document split retrieval authority. |
| Bridge/proxy | dopecon-bridge | OBSERVED | Adapter/proxy/event transport only; never PM/workflow authority. |
| Agent authority | no single repo-wide owner | UNKNOWN | `AGENTS.md` and `PROJECT.md` preserve unresolved agent authority. |
| PR Steward v1 | check-only review-intake gate | PROPOSED | Defined by this packet's docs, schemas, and future task packet. |
| Skip-second-supervisor rule | gate rule after embedded audit and PR Steward READY | PROPOSED | Governance policy only; no runtime automation here. |

## Conflict Handling

When a packet, prompt, or PR Steward summary sees conflicting sources, it must preserve the conflict in output instead of choosing the convenient story. Runtime truth wins over stale docs; task packets govern current scope and allowlists but cannot make unsupported runtime behavior true.
