---
id: fast-dev-os-runtime-dependency-cones
title: Fast Dev OS — Runtime Dependency Cones
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Cross-workstream collision matrix declaring which Fast Dev OS packets cannot parallelize. Used at packet-planning time to prevent concurrent edits to shared contracts and runtime surfaces.
---
# Fast Dev OS — Runtime Dependency Cones

## Relationship to governance

This document **operationalizes** [`codex-authority-refresh.md`](../governance/codex-authority-refresh.md) and AGENTS.md §6 architecture boundaries; it **does not override** them.

## Lane

**L2** — the collision matrix affects every packet's worktree + branch strategy.

## Why "cones"

Each packet's blast radius extends outward from the files it touches: caller code, schema consumers, downstream tests, dependent runtime services. A "dependency cone" is the set of all surfaces a given packet could affect by changing its targeted files. Two packets **collide** if their cones intersect — they cannot safely run in parallel branches.

## Collision matrix

| Workstream A | Workstream B | Collision class | Mitigation |
|--------------|--------------|-----------------|------------|
| Doctrine layer (`docs/03-reference/fast-dev-os/`) | Governance layer (`docs/03-reference/governance/`) | LOW (one-way: governance outranks doctrine) | Doctrine packets must not modify governance files; declared as invariant in TP. |
| Schema (`docs/03-reference/spec/dopetask/*`) | Any TP that uses `execution.agent` enum | HIGH (schema changes cascade) | Schema-extend TPs are serialized; never run concurrent with TPs that author new packets. |
| Doctrine layer | Doctrine layer | HIGH (overlapping ledgers + readme) | Doctrine packets in the same series are **serialized via depends_on**, never parallel. Stacked branches are allowed if depends_on is documented. |
| Service code (`services/<svc>/`) | Service code (different svc) | LOW | Distinct services can parallelize provided no shared schema / contract. |
| Service code (same svc) | Service code (same svc) | HIGH | Single service must not have concurrent TPs unless touching disjoint files; merge conflicts will surface. |
| Runtime config (`docker-compose*.yml`, `services/*/config/*`) | Runtime config | CRITICAL | Runtime config changes must serialize; concurrent edits break local + CI startup. |
| Dependency files (`pyproject.toml`, `package.json`) | Dependency files | CRITICAL | Dependency changes must serialize; concurrent edits cause version conflicts. |
| Tests (`tests/`) | Service code being tested | MEDIUM | OK to parallelize **if** the TPs touch disjoint test modules / fixtures. Tighten via TP allowlist. |
| `task-packets/INDEX.md` | `task-packets/INDEX.md` | HIGH | Index updates must serialize; the index is the single canonical packet registry. |
| `proof/` (existing entries) | `proof/` (new entries) | LOW | New PROOF directories don't collide with existing ones. `.gitignore` negation patterns may collide if both packets add similar patterns. |
| Branch protection / `.github/workflows/` | Any other TP | CRITICAL | CI / branch protection changes must run serially with full operator review. |

## Lane-to-cone heuristic (per project-constitution.md)

The lane taxonomy is canonical in `project-constitution.md`. The collision matrix below maps each lane to its blast radius and parallelizability:

| Lane | Use when | Reviewer | Proof |
|------|----------|----------|-------|
| **L0: Design only** | No repo mutation | None | Citations + UNKNOWNs |
| **L1: Docs / prompt / packet** | Governance docs, prompt packs, task templates | Optional | diff, docs check, schema check |
| **L2: Bounded implementation** | Small source/test/config with clear owner | Default off | targeted tests, diff, precommit |
| **L3: Runtime spine** | CLI, dopetask, task-orchestrator, RTE, PM writes | Yes if risk ≥ medium | focused tests + integration proof |
| **L4: Boundary-sensitive** | PM, memory, retrieval, bridge, Cockpit gates, agents | Yes | boundary audit + tests |
| **L5: Security / provider / secrets** | Auth, secrets, CI, provider behavior, live extraction | Yes (security reviewer) | security scan + official docs |
| **L6: Parallel backlog** | Multiple independent low/medium packets | Spot review | branch matrix + PR checks |

### Cone radius by lane

| Lane | Cone radius | Parallelizable? |
|------|-------------|-----------------|
| L0 | Read-only — no cone | YES (trivially; no mutation) |
| L1 | Docs only; consumers = readers | YES if different doc subtrees |
| L2 | Bounded implementation; consumers = tests + owner | YES if disjoint modules; NO if shared modules |
| L3 | Runtime spine (CLI, dopetask, task-orchestrator, RTE, PM writes); consumers = runtime callers | NO — serialize, mandatory audit if risk ≥ medium |
| L4 | Boundary-sensitive (PM, memory, retrieval, bridge, Cockpit gates, agents); consumers = cross-component | NO — serialize, mandatory audit |
| L5 | Security / provider / secrets; consumers = all callers + security posture | NO — serialize, security reviewer mandatory |
| L6 | Parallel backlog (multiple independent low/medium packets); consumers = per-packet | YES with spot review (each packet still serializes within its own lane) |

## Stacked PR pattern

When two packets in the same series share files (typical for doctrine layer), the second packet's branch is **stacked on the first packet's branch**, not branched from `origin/main`. The PR for the second packet shows the cumulative diff (both packets) until the first PR merges; after merge, the second PR's diff narrows to only the second packet's additions.

Reference: `TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK` was stacked on `TP-DMX-FDOS-004-AUTHORITY-REFRESH` because TP-FDOS-005's prompt content references `project-constitution.md` from TP-FDOS-004. Same pattern for TP-FDOS-006 stacked on TP-FDOS-005.

## Worktree discipline (per AGENTS.md §4)

- **One TP = one worktree** = one branch. Never reuse a worktree across packets.
- **Worktree path** convention: `/<operator code root>/dopemux-mvp-<series>-<NNN>-<slug>/`.
- **Branch** convention: `codex/<series>-<NNN>-<slug>` or `<implementer>/<series>-<NNN>-<slug>`.
- **Cleanup** when PR opens cleanly: remove worktree (record in PROOF.json `cleanup_status`).

## Pre-flight collision check (recommended)

Before opening a new packet, run:

```bash
# List active branches in this series
git branch -a --list 'codex/dmx-<series>-*' 'fdos/*' '<series>/*' 2>/dev/null

# List active worktrees
git worktree list

# Cross-check against task-packets/INDEX.md
grep -l '<series>' task-packets/INDEX.md
```

If any active branch in the same series touches the same allowlist paths, **serialize** — wait for that packet to merge or rebase your packet on top of it (stacked PR).

## Cross-references

- AGENTS.md §6 architecture boundaries: [../../../AGENTS.md](../../../AGENTS.md).
- Worktree lifecycle (AGENTS.md §4): [../../../AGENTS.md](../../../AGENTS.md).
- Authority order (AGENTS.md §2): [../../../AGENTS.md](../../../AGENTS.md).
- Governance: [`../governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md).
- Lane taxonomy: [`project-constitution.md`](project-constitution.md).

## Truth posture

> Collisions are not the worst case — silent collisions are. If a TP touches a file another open TP also touches, surface the conflict before running, not after merge.

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence.
