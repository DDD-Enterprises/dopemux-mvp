---
id: UNBUILT_FEATURES_AND_ROADMAP
title: Unbuilt Features And Roadmap
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-06'
last_review: '2026-02-08'
next_review: '2026-05-10'
prelude: Unbuilt Features And Roadmap (explanation) for dopemux documentation and
  developer workflows.
---
# Unbuilt Features & Roadmap Catalog (The "Lost Futures")

**Date**: 2026-02-06
**Scope**: Features specified in ADRs/READMEs where implementation maturity differs from documented intent.
**Status**: Code-truth classification uses `Implemented`, `Partially Implemented`, and `Planned`.

## Verification Status (Code-Truth, 2026-02-06)

- Implemented: Core event bus, task-orchestrator runtime, and all seven agent module files exist.
- Partially Implemented: Agent readiness, auto-resume reliability, and event-adapter depth are incomplete.
- Planned: Bio-feedback integration remains roadmap-level work.

## 1. Executive Summary

Our deep dive revealed a significant gap between the *documented vision* and the *implemented reality*. The core "Two-Plane Architecture" is live, but advanced orchestration and ADHD automation remain uneven across components.

**Top 3 Remaining Capability Gaps:**
1. **The 4-Stage Workflow** (ADR-197): Stage 1/2 (`Idea`/`Epic`) runtime is implemented; stage 3/4 production hardening and end-to-end integration depth remain incomplete.
2. **Auto-Resume** (ADR-180): Core resume paths exist, but quality and integration hardening are incomplete.
3. **Cognitive Guardian**: Module exists, but full intervention quality and production hardening are incomplete.

---

## 2. Implementation Reality Matrix

| Feature | Source | Status | Description |
|:---|:---|:---:|:---|
| **Cognitive Guardian** | `agents/README` | Partially Implemented | Agent module exists; intervention behavior needs production hardening. |
| **TwoPlaneOrchestrator** | `agents/README` | Partially Implemented | Module exists; authoritative cross-plane enforcement remains incomplete. |
| **TaskDecomposer** | `agents/README` | Partially Implemented | Module exists; PRD-to-task quality and validation depth need hardening. |
| **DopemuxEnforcer** | `agents/README` | Partially Implemented | Module exists; architecture policy enforcement is not fully operationalized. |
| **ToolOrchestrator** | `agents/README` | Partially Implemented | Module exists; intelligent model routing maturity remains limited. |
| **WorkflowCoordinator** | `agents/README` | Partially Implemented | Module exists; end-to-end workflow orchestration depth is incomplete. |
| **Auto-Resume** | `ADR-180` | Partially Implemented | Orphan detection and resume commands exist; reliability and UX hardening pending. |
| **Idea -> Epic Flow** | `ADR-197` | Partially Implemented | Stage-1/Stage-2 workflow runtime is active; deeper integration and production hardening remain. |
| **Event Adapters** | `ADR-207` | Partially Implemented | Adapter modules exist, but full event-driven maturity remains incomplete. |
| **Bio-Feedback** | `adhd-engine` | Planned | Hardware integration remains roadmap-level only. |

---

## 3. Deep Dive into Missing Systems

### 👻 Agent Readiness Gap (Modules Present, Quality Incomplete)
All seven agent module files are present in `services/agents/`, but several remain partially implemented in runtime quality, orchestration depth, and production hardening.
- **Impact**: The system has more than passive memory support, but guidance/enforcement behavior is not yet uniformly reliable.

### 🚧  The Workflow Hardening Gap (ADR-197)
We designed a beautiful 4-stage flow:
1. **Idea** (Unstructured)
2. **Epic** (Structured)
3. **Task** (Executable)
4. **Execution** (Tracked)

**Reality**: Stage 1 & 2 runtime now exist in active code paths (`/api/workflow/ideas`, `/api/workflow/epics`, promotion flow, CLI commands), with persistence via workflow custom-data categories.
**Remaining Gap**: Full production-depth integration from stage 1/2 through stage 3/4 still needs broader end-to-end validation and operational safeguards.

### 💔 The Orchestration Gap (ADR-207)
The `task-orchestrator` service exists with adapter implementations, but event-driven maturity and integration depth still lag the architecture intent.
**Current State**: Adapter modules are present (`conport_adapter`, enhanced orchestrator paths), but complete contract hardening and coverage are incomplete.
**Consequence**: Dependency analysis and cross-service signal quality can still be brittle in edge scenarios.

---

## 4. Recommendations for Next Phase

1. **Harden and Extend the "Idea Bucket" (ADR-197)**: Stage-1/Stage-2 runtime is present; prioritize end-to-end integration, operational guardrails, and production test depth.
2. **Harden Auto-Resume (ADR-180)**: Stabilize and test current resume paths end-to-end rather than treating feature as absent.
3. **Productionize Cognitive Guardian**: Convert current partial implementation into validated intervention workflows with measurable behavior.

---
*Generated by Deep Dive Agent - Phase 5 Analysis*
