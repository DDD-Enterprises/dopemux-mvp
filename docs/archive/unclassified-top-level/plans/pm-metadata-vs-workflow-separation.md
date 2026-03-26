# Implementation Plan: PM Metadata vs. Workflow-Significant Writes

## 1. Objective & Scope
The objective is to operationalize the boundaries defined in `ADR-PM-001` (Canonical Task Object) and `ADR-PM-003` (Storage - Derived vs. Mirrored). The Dopemux PM Plane is the **Canonical Authority** for task lifecycle state, while integrations like Leantime act as **Mirrored/Projection Paths**. 

This plan separates **Workflow-Significant Writes** (which mutate canonical state and require stale-write protection) from **PM Metadata Writes** (which passively update contextual fields without bumping task versions). It also implements the `LeantimeReflection` pattern to prevent webhook sync loops.

---

## 2. Phase 1: Canonical PM Store Updates (`src/dopemux/pm/`)

We will update the core PM abstractions to natively support passive metadata patching and codify the boundary between workflow and metadata fields.

### 2.1 Formalize Field Boundaries (`src/dopemux/pm/models.py`)
Add explicit constants to define the field domains:
```python
# Fields requiring optimistic concurrency control (version bumps)
WORKFLOW_SIGNIFICANT_FIELDS = frozenset({"status", "version", "blocked_reason", "dependencies"})

# Fields supporting a last-write-wins update strategy
METADATA_ONLY_FIELDS = frozenset({"title", "description", "assignee", "labels", "milestone", "meta"})
```

### 2.2 Modifications to `store.py`
1.  **Update `PMTaskStore` Protocol:**
    Add a new method signature:
    ```python
    def patch_metadata(self, task_id: str, patch: dict[str, Any]) -> PMTask:
        """Apply passive metadata updates without bumping the canonical version."""
        pass
    ```

2.  **Implement in `InMemoryPMTaskStore`:**
    *   **Logic:** Retrieve the task by `task_id`. If not found, raise `TaskNotFoundError`.
    *   Iterate through the `patch` dictionary.
    *   **Crucial Rule:** Only apply updates to keys present in `METADATA_ONLY_FIELDS`. 
    *   Silently ignore (or actively pop) any keys from `WORKFLOW_SIGNIFICANT_FIELDS` (especially `version` and `status`).
    *   Update `updated_at_utc`.
    *   Do **not** increment `version`. Do **not** check `expected_version` or `idempotency_key`.
    *   Return a copy of the updated `PMTask`.

### 2.3 Unit Tests (`tests/unit/pm/test_pm_store.py`)
1.  **Test `patch_metadata` success:** Verify allowed fields (`title`, `description`) are updated correctly.
2.  **Test version preservation:** Verify that calling `patch_metadata` does **not** increment `task.version`.
3.  **Test restricted fields:** Verify that attempting to patch `status` or `version` via `patch_metadata` is completely ignored.
4.  **Test missing task:** Verify `patch_metadata` raises `TaskNotFoundError` if the ID does not exist.

---

## 3. Phase 2: Orchestrator Integration & Reflection (`services/task-orchestrator/`)

We will update the webhook handling logic to intelligently route incoming Leantime events based on whether they are echoes, metadata patches, or workflow overrides.

### 3.1 Webhook Parsing Logic (`services/task-orchestrator/app/api/webhooks.py` or equivalent)
When a Leantime webhook payload is received:

1.  **Echo Check (Reflection Matching):**
    *   Compare the incoming webhook state against the local `PMTask`'s most recent `LeantimeReflection`.
    *   *If the incoming state exactly matches the `LeantimeReflection`*: **DROP** the event. This is an echo of an outbound sync. Log as `sync_echo_dropped`.

2.  **State Classification & Mixed Payload Handling:**
    If it's not an echo, diff the incoming payload against the local canonical task state:
    *   *Did ANY `WORKFLOW_SIGNIFICANT_FIELDS` change?* 
        *   **Action:** Treat the ENTIRE payload as a Workflow Override Attempt. 
        *   **Rule:** Route to `store.transition()`. If the transition fails due to a stale `expected_version`, the entire payload (including metadata changes) is **REJECTED**. This prevents data divergence where a task gets a new title but an outdated status.
    *   *Did ONLY `METADATA_ONLY_FIELDS` change?* 
        *   **Action:** Treat as a pure Metadata Patch.
        *   **Rule:** Route to `store.patch_metadata()`. The update succeeds on a last-write-wins basis without version checking.

---

## 4. Phase 3: Documentation Updates (`docs/planes/pm/`)

Codify this contract in the PM architecture documentation.

### 4.1 Create `docs/planes/pm/pm-metadata-vs-workflow.md`
This document will serve as the definitive guide for field classification and sync behavior.

**Structure:**
*   **Header:** Title, Status (Active), Context.
*   **Field Classification Boundary:**
    *   *Workflow Authority (Strict):* `status`, `version`, `blocked_reason`, `dependencies`. Mutated ONLY via `PMTransitionRequest`.
    *   *Metadata Authority (Passive):* `title`, `description`, `assignee`, `labels`. Mutated via `patch_metadata`.
*   **The Reflection Pattern (Infinite Loop Prevention):**
    *   Explain how `LeantimeReflection` records outbound syncs.
    *   Include a flow chart explaining the Echo Drop sequence.
*   **Stale Write Handling & Mixed Payloads:**
    *   Explicitly define the atomic rule: "If a webhook contains workflow-significant changes, the entire update is subject to strict optimistic locking. If it fails, the entire update is rejected to prevent divergence. Pure metadata updates bypass version checks."

### 4.2 Link from `pm-architecture.md`
Add a reference and brief summary of this new document in the main `pm-architecture.md` file under the Storage/State section.

---

## 5. Rollout & Verification Strategy

1.  **Implement Phase 1:** Add constants, add `patch_metadata`, and ensure all unit tests pass.
2.  **Implement Phase 3:** Write the documentation to lock in the contract.
3.  **Implement Phase 2:** Update the webhook routing logic.
4.  **Integration Testing:** 
    *   Simulate a Leantime webhook that only changes a title. Verify canonical version stays the same.
    *   Simulate a mixed webhook (status + title change) against a stale version. Verify the entire update is rejected.
    *   Simulate a standard outbound sync, then simulate the resulting inbound webhook. Verify the `LeantimeReflection` correctly drops the echo.