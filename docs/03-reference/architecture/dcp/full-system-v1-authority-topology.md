---
id: dcp-full-system-v1-authority-topology
title: "DCP Full-System V1 Authority Topology"
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-08-27'
last_review: '2026-08-27'
next_review: '2026-09-27'
status: accepted
prelude: Canonical P0 map of full-system writers, DCP coordination duties, exclusions, and separate activation gates.
---

# DCP Full-System V1 Authority Topology

## Governing rule

DCP coordinates evidence and policy. It does not become canonical writer for
systems it coordinates. Current runtime/source truth outranks projections and
historical design prose.

| Domain | Canonical writer/authority | DCP may | DCP may not |
|---|---|---|---|
| PM metadata | Leantime | Reference records | Write PM state |
| Workflow state | Task Orchestrator | Read blockers and legal state | Transition items |
| Decisions/progress/context | ConPort | Retrieve revision-bound snapshots | Overwrite canonical context |
| Chronicle | dope-memory | Retrieve historical receipts | Promote history into decisions |
| Retrieval | dope-context | Discover candidates with provenance | Treat hits as dereferenced truth |
| Second Brain | Existing canonical planes; SB output is derived | Compile non-canonical read models | Write back or overrule sources |
| Audit | Independently certified auditor | Bind exact request, receipt, result | Mutate repo/task or infer identity |
| GPT facade | Read-only facade | Expose six named reads | Add lifecycle/write/provider seams |
| Merge/activation | Human operator and current governance | Report gate state | Auto-advance |

Bridge and cache layers are transport/projection only. `UNKNOWN` and
`CONFLICTING` remain visible. No subsystem gains authority merely because paths
are disjoint or a schema validates.

## Activation

Contract acceptance, implementation, validation, audit, merge, and runtime
enablement are separate gates in that order. PASS is evidence for a decision,
not the decision itself.

## Retained named gate

GPT-5.5 named-gate requirement remains in force until exact supersession.
GPT-5.6 does not substitute for it.
