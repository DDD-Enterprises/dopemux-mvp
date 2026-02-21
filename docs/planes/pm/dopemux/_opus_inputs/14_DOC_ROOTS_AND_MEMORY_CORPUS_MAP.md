---
id: 14_DOC_ROOTS_AND_MEMORY_CORPUS_MAP
title: 14 Doc Roots And Memory Corpus Map
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: 14 Doc Roots And Memory Corpus Map (explanation) for dopemux documentation
  and developer workflows.
---
# 14_DOC_ROOTS_AND_MEMORY_CORPUS_MAP

## Table 1: Doc Roots
| Root Dir               | Purpose Guess                           | Notes                                                                        |
| :--------------------- | :-------------------------------------- | :--------------------------------------------------------------------------- |
| `docs/planes`          | Architectural stratification            | Primary source for PM/Cognitive/Search plane definitions.                    |
| `docs/spec`            \| Protocol and data specifications        \| Contains authoritative `dope-memory` v1 specs.                               |
| `docs/systems`         \| Component-level documentation           \| Detailed breakdown of `conport`, `task-orchestrator`, etc.                   |
| `docs/task-packets`    | Execution units and instructions        | Contains binding invariants for specific work chunks (e.g., TP-PM-ARCH-04B). |
| `docs/archive`         | Legacy and completed history            | Useful for audit trails but risky for current contract drift.                |
| `docs/investigations`  | Ad-hoc research and root cause analysis | Contextual but non-normative.                                                |
| `docs/best-practices`  | Usage guidelines                        | Operational guidance rather than system invariants.                          |
| `docs/projects`        \| Feature-specific tracking               \| Transient until merged into `systems` or `planes`.                           |
| `docs/pm`              \| Project Management specific             \| Likely overlaps with `planes/pm`.                                            |
| `docs/troubleshooting` | Known issues and fixes                  | Operational/Support signal.                                                  |

## Table 2: Memory/PM High-Signal Docs
| Path                                                                                                   | Date       | Category       | Why it matters                                            | Key Headings                                                 |
| :----------------------------------------------------------------------------------------------------- | :--------- | :------------- | :-------------------------------------------------------- | :----------------------------------------------------------- |
| `docs/planes/pm/dopemux/OPUS-CROSS-PLANE-AUDIT.md`                                                     | 2026-02-12 | Audit/Contract | Defines cross-plane boundaries and current gaps.          | Objective, Scope, Invariants, Locked Decisions               |
| `docs/spec/dope-memory/v1/01_architecture.md`                                                          | 2026-02-12 | Spec           | Authoritative ADHD Engine / dope-memory topology.         | Goals, Key Concepts, Component Topology                      |
| `docs/spec/dope-memory/v1/02_data_model_sqlite.md`                                                     | 2026-02-12 | Schema         | Specific SQLite table schemas for local memory.           | Schema Overview, Tables, Invariants                          |
| `docs/spec/dope-memory/v1/07_mcp_contracts.md`                                                         | 2026-02-12 | Contract       | Binding MCP server communication protocols.               | Overview, Capabilities, Protocol Invariants                  |
| `docs/task-packets/TP-PM-ARCH-04B.md`                                                                  | 2026-02-12 | Invariant      | Opus-locked rules for canonical PM events.                | Hard Invariants, Canonical Event Types, Implementation Notes |
| `docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/06_DOPE_MEMORY_PROMOTION_RETENTION_PROVENANCE.md` | 2026-02-13 | Provenance     | Defines how facts move from cognitive to PM plane.        | Promotion Rules, Retention Policy, Provenance Fields         |
| `docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/03_STORE_WRITE_OWNERSHIP_MATRIX.md`               | 2026-02-13 | Authority      | Deterministic map of which service writes to which store. | Write Authority, Ownership Conflicts, Mutability Rules       |
| `docs/planes/pm/_evidence/PM-INV-01_TASK_SCHEMA_ANALYSIS.md`                                           | 2026-02-12 | Analysis       | Deep dive into TaskX vs Leantime schema drift.            | Objective, Findings, Recommended Fixes                       |
| `docs/systems/conport/custom-instructions/mem4sprint-schema-and-patterns.md`                           | 2026-02-12 | Pattern        | Practical implementation patterns for ConPort storage.    | Persistence Patterns, Event Invariants, Query Bounds         |

## Docs not included and why
- `docs/archive/completed-projects/*`: Redundant. Replaced by `systems/` or `planes/` current state.
- `docs/investigations/*`: Too transient. Findings should be in `OPUS-CROSS-PLANE-AUDIT.md` or similar.
- `docs/troubleshooting/*`: Out of scope for Master Contract (operational).

## Open gaps (UNKNOWN items)
- **UNKNOWN**: `search plane` depth. Most docs focus on PM and Cognitive planes. Search plane is referenced but lacks a dedicated `docs/spec/search-plane`.
- **UNKNOWN**: `identity plane` authority. Who owns the canonical `user_id`/`workspace_id` mapping? `docs/systems/multi-workspace/README.md` is light on invariants.
- **Command to confirm**: `rg "identity plane|search plane" docs -S` and `find docs/spec -iname "*search*"`
