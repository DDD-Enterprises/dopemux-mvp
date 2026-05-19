---
id: audience-personas
title: Audience Personas
type: explanation
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Repo-grounded Dopemux audience personas with authority and limitation notes.
---
# Audience Personas

These personas describe audiences the repository evidence supports. They are
not market claims about production readiness, autonomous learning, or a unified
assistant.

## Primary Persona: Operator-Maintainer

The operator-maintainer works inside the Dopemux workspace and needs a control
plane for startup, routing, execution handoff, service checks, and repo-aware
workflow decisions.

| Need | Dopemux fit | Boundary |
| --- | --- | --- |
| Start and inspect the workspace | Implemented through the `dopemux` CLI and compose-backed docs | Live health still requires runtime validation. |
| Route work to the right system | Implemented as split-authority guidance and PM adapters | The CLI does not own every downstream truth domain. |
| Preserve proof | Implemented through Task Packet discipline and proof docs | Proof does not replace validation that was NOT_RUN. |

## Secondary Persona: Documentation Maintainer

The documentation maintainer needs repo-faithful docs that do not overwrite
runtime truth with old architecture prose or cleaner marketing language.

| Need | Dopemux fit | Boundary |
| --- | --- | --- |
| Find the trusted docs | Implemented through source map, gap register, and indexes | Historical docs can remain contradictory. |
| Update docs safely | Implemented through docs validators and packet allowlists | Full-repo docs hygiene still has remaining debt. |
| Preserve UNKNOWN | Implemented through governance and handoff rules | UNKNOWN is not a defect until evidence exists. |

## Secondary Persona: PM Workflow Integrator

The PM workflow integrator needs to know which system owns which PM action.

| Need | Dopemux fit | Boundary |
| --- | --- | --- |
| Update metadata | Leantime is the passive PM metadata authority | Task Orchestrator is not all PM state. |
| Move workflow state | task-orchestrator owns workflow-significant transitions | Leantime mirrors do not prove workflow legality. |
| Record decisions/progress | ConPort owns structured decisions and progress | dope-memory receipts are historical mirrors. |

## Secondary Persona: Repo Truth Auditor

The repo truth auditor uses Repo Truth Extractor and source inspection to
separate implemented behavior from drift, advisory docs, and generated
artifacts.

| Need | Dopemux fit | Boundary |
| --- | --- | --- |
| Extract repo evidence | Repo Truth Extractor produces evidence artifacts | Artifacts do not outrank runtime code/config/tests. |
| Inspect retrieval output | dope-context provides derived code/docs retrieval | Retrieval output is not source truth. |
| Close drift | Runtime validation can close specific drift | Docs-only packets cannot close runtime drift. |

## Adjacent Persona: ADHD-Aware Operator

The ADHD Engine supports operator state, workload, recommendations, and
context-adjacent surfaces.

| Need | Dopemux fit | Boundary |
| --- | --- | --- |
| Reduce operator overhead | ADHD Engine is a support component | It does not own PM, memory, or ConPort truth. |
| Keep work visible | Operator docs and proof templates help preserve context | Persistence authority for some support surfaces is UNKNOWN. |

## Non-Target Claims

Dopemux should not be positioned as:

- a monolithic assistant
- a single autonomous agent runtime
- a production PM replacement
- a unified memory product
- a bridge-owned decision system

Those claims exceed the inspected repository evidence.
