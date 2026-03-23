---
id: pm-metadata-vs-workflow
title: PM Metadata vs Workflow Authority
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-22'
last_review: '2026-03-22'
next_review: '2026-06-22'
prelude: Field classification boundary and Stale Write Handling rules defining PM Metadata vs Workflow Authority.
---

# PM Metadata vs Workflow Authority

This document operationalizes the boundaries defined in `ADR-PM-001` (Canonical Task Object) and `ADR-PM-003` (Storage - Derived vs. Mirrored).

The Dopemux PM Plane acts as the **Canonical Authority** for task lifecycle state, while external integrations (like Leantime) act as **Mirrored/Projection Paths**. To enforce this, we strictly separate **Workflow-Significant Writes** from **PM Metadata Writes**.

## Field Classification Boundary

The task schema is divided into two distinct domains of authority:

1. **Workflow Authority (Strict Transitions)**
   - **Fields:** `status`, `version`, `blocked_reason`, `dependencies`.
   - **Contract:** These fields mutate the canonical state machine. They **MUST** be processed via a `PMTransitionRequest` utilizing optimistic concurrency control (`expected_version`) and idempotency (`idempotency_key`).
   - **Resolution:** If a mirror (e.g., Leantime webhook) attempts to override these fields and the local canonical version has advanced past the mirror's known state, the workflow override is **REJECTED** as a stale write.

2. **Metadata Authority (Passive Patches)**
   - **Fields:** `title`, `description`, `assignee`, `labels`, `milestone`, `meta`, `linked_ids`, `refs`, `source_task_id`.
   - **Contract:** These fields provide context but do not alter the workflow state machine. They are updated via passive patches (`patch_metadata`).
   - **Resolution:** Metadata patches do **not** increment the canonical `version` and do **not** require strict stale-write protection. They are accepted on a last-write-wins basis.

## The Reflection Pattern (Infinite Loop Prevention)

Bidirectional sync introduces the risk of infinite echo loops (e.g., Dopemux updates Leantime -> Leantime fires a webhook back to Dopemux -> Dopemux updates Leantime).

To prevent this, the Task Orchestrator implements the **Reflection Pattern** using a `LeantimeReflection` object on the task.

1. **Outbound Sync:** When Dopemux pushes a state change to Leantime, it records the exact state it pushed as a `LeantimeReflection`. It emits a `pm.sync.succeeded` event.
2. **Inbound Webhook:** When a webhook arrives from Leantime, the Orchestrator compares the incoming state to the `LeantimeReflection`.
3. **Echo Drop:** If the webhook state exactly matches the reflection, the event is recognized as an echo of our own outbound sync and is **DROPPED**.

## Stale Write Handling & Mixed Payloads

When a non-echo webhook arrives from a mirrored system, its payload is diffed against the current local canonical state.

Handling follows an atomic, fail-closed rule for mixed payloads:

*   **Scenario A: Pure Metadata Patch**
    *   *Condition:* The diff shows changes ONLY to `METADATA_ONLY_FIELDS`.
    *   *Action:* The update is processed as a passive patch. It succeeds regardless of the mirror's version awareness.
*   **Scenario B: Workflow Override (Mixed or Pure)**
    *   *Condition:* The diff shows changes to ANY `WORKFLOW_SIGNIFICANT_FIELDS` (e.g., `status` changed).
    *   *Action:* The **ENTIRE payload** is treated as a workflow transition and subjected to strict optimistic locking (`expected_version` check).
    *   *Resolution:* If the local canonical version has advanced, the **ENTIRE update is REJECTED**, including any metadata changes bundled within it. This prevents split-brain divergence where a task receives a new title from the mirror but retains an outdated status locally.
