---
id: authority-boundaries
title: Authority Boundaries
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Reference matrix for Dopemux canonical writers, derived views, and non-authority surfaces.
---
# Authority Boundaries

Use this reference before writing docs, routing PM updates, or interpreting
retrieval/extraction output. Authority is per domain.

## Boundary Matrix

| Domain | Canonical or strongest observed authority | Derived/supporting surfaces | Must Not Own |
| --- | --- | --- | --- |
| Operator control | `dopemux` CLI | compose, registry, local configs | PM truth, external execution after handoff |
| Execution after handoff | external `dopetask` through `scripts/dopetask` | `scripts/taskx` shim | PM metadata, workflow legality, memory |
| PM metadata | Leantime | leantime-bridge, bridge-safe PM routing | workflow legality, decisions, progress context |
| Workflow transitions | Task Orchestrator | bridge custom-data persistence, Leantime status mirrors | all PM state, ConPort authority, dope-memory chronicle |
| Decisions/progress/context | ConPort | dopecon-bridge `/kg/*` proxy views, PM adapters | passive PM metadata, workflow legality |
| Historical receipts | dope-memory | PM mirror receipts, event projections | current PM state, all memory |
| Code/docs retrieval | dope-context | ConPort retrieval where applicable | source truth for retrieved files |
| Bridge/proxy/event transport | dopecon-bridge | Redis event bus, upstream adapters | canonical task, workflow, PM, decision, progress, memory, retrieval |
| Operator support | ADHD Engine | bridge and ConPort projections | PM truth, ConPort authority, dope-memory authority |
| Extraction/audit | Repo Truth Extractor | generated reports and proof artifacts | runtime truth or service authority |
| Agents | `UNKNOWN` | `services/agents`, `src/dopemux/agent_orchestrator.py`, task-orchestrator agents | PM truth or repo-wide authority without proof |

## Rules

- Name the canonical writer before making a write.
- Treat a mirror as a receipt only when the canonical writer is named.
- Treat retrieval output as derived evidence.
- Treat dopecon-bridge routes as operational paths, not source truth.
- Treat Repo Truth Extractor artifacts as evidence, not stronger than runtime.
- Preserve `UNKNOWN` when ownership is not proven.

## Examples

| Question | Authority path |
| --- | --- |
| Change a task title or assignee | Leantime metadata path |
| Move a work item through workflow | task-orchestrator transition path |
| Record a project decision | ConPort decision/progress path |
| Preserve historical context | dope-memory chronicle path |
| Find code/docs context | dope-context retrieval, then inspect source |
| Route a compatibility call | dopecon-bridge, with upstream authority named |
| Audit repo architecture | Repo Truth Extractor, with runtime truth still stronger |

## Required Labels

Use these labels in proof and docs when authority is not direct:

- `canonical`: direct owner for this domain slice.
- `mirror`: receipt or reflection from a canonical writer.
- `proxy`: transport or adapter path.
- `derived`: retrieval, report, index, summary, or projection.
- `UNKNOWN`: unresolved ownership or runtime authority.
- `NEEDS_REPO_VERIFICATION`: plausible but not exercised in runtime validation.
