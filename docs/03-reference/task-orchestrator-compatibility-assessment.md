# Dopemux Task-Orchestrator Upstream Compatibility Assessment

## 1. Executive Summary

This document provides a comprehensive, read-only compatibility assessment of the upstream plugin repository `claude-plugins/task-orchestrator` with the Dopemux architecture. 

Historically, task-orchestrator has evolved from a simple Kotlin-based MCP wrapper (`server.py`) to a sophisticated workflow engine (v3.8.0) that utilizes composable traits, note-based gate enforcement, and automated Hook injection. Dopemux currently implements a robust, concurrent Python-based dispatcher (`src/dopemux/claude/native_hooks.py`) and a multi-worktree execution model. 

### Core Recommendation
**Do not directly replace or hot-swap Dopemux's native hook adapter with the upstream Node.js hook suite.** Instead, maintain the Python-based `native_hooks.py` as the canonical dispatcher, and bridge upstream v3 capabilities (such as the schema workflow and composable traits) by translating the hook context injection into Python or orchestrating the Node.js hooks in an isolated sandbox. Upstream's singleton assumptions clash with Dopemux's parallel worktree isolation, requiring explicit workspace isolation and provenance tracking.

---

## 2. Upstream Directory & Skill Catalog

The upstream plugin repository located at `claude-plugins/task-orchestrator` is structured into three primary components: `skills/`, `hooks/`, and `output-styles/`.

```
claude-plugins/task-orchestrator/
  ├── hooks/
  │   ├── hooks-config.json
  │   ├── session-start.mjs
  │   ├── pre-plan.mjs
  │   ├── post-plan.mjs
  │   ├── subagent-start.mjs
  │   └── hooks-config.json
  ├── output-styles/
  │   └── workflow-orchestrator.md
  └── skills/
      ├── batch-complete/
      ├── create-item/
      ├── dependency-manager/
      ├── manage-schemas/
      ├── post-plan-workflow/
      ├── pre-plan-workflow/
      ├── quick-start/
      ├── schema-workflow/
      ├── status-progression/
      └── work-summary/
```

### 2.1 The 10 Bundled Skills
Each skill provides specialized interactive prompts and workflow guidance designed to teach the model how to operate task-orchestrator tools effectively.

1. **`quick-start`**: Interactive onboarding. It detects whether a workspace is active or empty by calling `get_context()` and guides the model down a "Fresh-Start Path" (learning plan-mode, atomic creation, and roles) or an "Orientation Path" (providing active dashboards and unblocking steps).
2. **`pre-plan-workflow`**: Internal skill triggered during `EnterPlanMode`. It inspects the current database state (`get_context()`) and reads `.taskorchestrator/config.yaml` to discover required schemas and set the **definition floor** before planning begins, ensuring the plan doesn't duplicate existing items and accounts for required documentation notes.
3. **`post-plan-workflow`**: Internal skill triggered during `ExitPlanMode` (after plan approval). It manages the **materialization** phase, creating the work items, tags, and dependencies atomically using `create_work_tree`, then dispatches implementation agents with specific item UUIDs and guidance pointers.
4. **`schema-workflow`**: Drives schema-tagged work items through their lifecycle. It dynamically queries `get_context(itemId=...)` to check `expectedNotes`, `missing` required notes, and `guidancePointer` authoring instructions, forcing the model to fill notes before transitioning.
5. **`manage-schemas`**: Interactive CRUD manager for `.taskorchestrator/config.yaml`. Supports creating, viewing, editing, deleting, and validating schemas.
6. **`batch-complete`**: Facilitates the recursive completion of entire work item trees.
7. **`create-item`**: Context-aware item creation. It automatically infers priority, parent containers, and schema tags from the conversation context.
8. **`dependency-manager`**: Handles wiring, querying, and auditing the DAG of dependency edges (`BLOCKS` edges) between work items.
9. **`status-progression`**: Diagnostic and progression utility. It guides stuck or blocked items through intermediate transitions.
10. **`work-summary`**: Compiles comprehensive dashboards detailing active work, blocked items, root epics, and recommended next items.

### 2.2 Hook Events and Scripts
The upstream repo registers JS-based scripts in `hooks-config.json` that hook directly into Claude Code lifecycle events:

*   **`SessionStart`** (`session-start.mjs`):
    Injects initial v3 workflow context, reminding the model of the available 13 tools, active/stalled status queries, and the parent-child hierarchy.
*   **`PreToolUse`** / `matcher: EnterPlanMode` (`pre-plan.mjs`):
    Injects instructions telling the model to immediately run `task-orchestrator:pre-plan-workflow` to check existing work and discover config schemas before drafting the plan.
*   **`PostToolUse`** / `matcher: ExitPlanMode` (`post-plan.mjs`):
    Injects instructions telling the model to execute `task-orchestrator:post-plan-workflow` to materialize the plan into DB items and wire dependencies before coding starts.
*   **`SubagentStart`** / `matcher: *` (`subagent-start.mjs`):
    Crucial guidance injection for spawned subagents. Instructs them to **transition immediately** to `work` role using `advance_item`, fetch the phase-gated implementation guidance using `get_context(itemId=...)`, fill the required notes, and only then start coding.

### 2.3 Output Style (`workflow-orchestrator.md`)
The output style enforces strict formatting and behavior patterns:
*   **Visual Conventions**: Mandates the use of status symbols (`✓` terminal, `◉` work/review, `⊘` blocked, `○` queue, `—` cancelled) and unicode-anchored markdown layouts (dashboards, narration lines prefixed with `↳`, blockquotes for `guidancePointer`).
*   **Delegation Rules**: Defines model selection tiers (Haiku for bulk ops/materialization, Sonnet for implementation/testing, Opus for complex architecture) and enforces a strict **"Never make 3+ MCP calls in a single turn"** rule, delegating bulk ops via Haiku to keep the orchestrator's context window clean.
*   **Separation of Concerns**: Differentiates between cross-session persistent state (MCP work items in SQLite) and ephemeral session progress (TUI/terminal session tasks).

---

## 3. Underlying Architectural Assumptions

Upstream task-orchestrator is built upon several foundational constraints that shape its runtime:

1.  **Single-Agent / Singleton Context**:
    Upstream assumes a single primary Claude session driving the workspace. The containerized MCP stdio wrapper runs as a singleton per workspace, locking the database during operations. If multiple parallel processes attempt to run standard stdio commands concurrently, the singleton locks and kills prior containers (enforced by the `task-orchestrator-current-stdio.sh` preflight script).
2.  **Claim-then-Advance Lifecycle**:
    Items must be explicitly "claimed" (attributing `claimed_by` and setting an expiration) before they can be transitioned. Transitions operate through a gated state machine: `queue` → `work` → `review` → `terminal` (`terminal` acts as the done state). Each transition checks note completion.
3.  **Strict File-Based Configuration**:
    Note schemas must be declared in `.taskorchestrator/config.yaml`. The schema-workflow is entirely dynamic—it parses the config file to determine what note keys are required at each phase, enforcing soft or hard gates depending on the `required: true/false` attribute.
4.  **Synchronous Note Gating**:
    Advancement triggers (`start`, `complete`, etc.) are synchronous validation gates. An item cannot transition from `queue` to `work` if any queue-phase required notes are absent, and cannot transition to `terminal` if the `proof-bundle` is missing.

---

## 4. Gaps and Compatibility Challenges with Dopemux

Integrating the upstream task-orchestrator into Dopemux reveals four key compatibility gaps:

### Gap 1: Worktree Parallelism vs. Stdio Singleton
*   **Upstream Assumption**: A single, local workspace utilizing a single task-orchestrator DB singleton.
*   **Dopemux Reality**: Dopemux supports **parallel worktrees** running concurrently (e.g., active developer worktrees under `.claude/worktrees/`). 
*   **Collision**: The upstream wrapper's multi-spawn singleton check (`docker run --name task-orchestrator-${workspace_id}`) prevents multiple active containers from locking the same DB. If two parallel Dopemux worktrees run tasks, the second container launch will forcefully kill the first container. If both point to the same host database without distinct workspace mapping, write locks and race conditions will occur.

### Gap 2: JavaScript Node Hooks vs. Python `native_hooks.py` Dispatcher
*   **Upstream Assumption**: A Node-based Claude Code hook environment executing shell-based JS scripts (`*.mjs`).
*   **Dopemux Reality**: Dopemux has an established, highly sophisticated Python-based hook dispatcher in `src/dopemux/claude/native_hooks.py`, tracking LiteLLM, workflow kernels, and active stop-gate checkpoints.
*   **Collision**: Registering the upstream `hooks-config.json` directly would completely override or bypass the Dopemux `native_hooks.py` dispatcher. Having two competing hook systems active simultaneously results in conflicting context injections, redundant validation passes, and execution hangs.

### Gap 3: MetaMCP Role Filtering and Stdio Proxies
*   **Upstream Assumption**: The task-orchestrator is exposed directly to the model as a top-level stdio MCP server.
*   **Dopemux Reality**: Dopemux routes MCP requests through proxies and MetaMCP role-filtering layers, managing which tools are exposed to which subagent (e.g. limiting write tools to specific sandboxes).
*   **Collision**: The upstream skills assume the model has unrestricted access to all 13/14 tools. If MetaMCP restricts tools (e.g., denying `manage_items` to a research model), the upstream skills (like `post-plan-workflow` or `quick-start`) will crash or fail silently.

### Gap 4: ADHD-Shaped Context vs. Workflow-Orchestrator Output Styles
*   **Upstream Assumption**: Strict `workflow-orchestrator.md` markdown styles and progress indicators.
*   **Dopemux Reality**: The Dopemux ADHD Engine has its own context manager (`src/dopemux/adhd/context_manager.py`) and error-formatting system designed to focus the agent's attention and avoid ambient cognitive noise.
*   **Collision**: Both systems inject comprehensive dashboards and status boxes at session startup. Dual injection will lead to prompt bloat, token wastage, and cognitive drift as the model tries to satisfy two distinct layout formatting instructions.

---

## 5. Actionable Integration Recommendations

To sustainably bridge upstream v3 capabilities into Dopemux:

1.  **Port Hook Context Logic to `native_hooks.py`**:
    Instead of executing Node.js `*.mjs` hook scripts, port their context-injection logic directly into Dopemux's Python dispatcher. For example:
    *   During `SessionStart` in `native_hooks.py`, append the task-orchestrator tool-surface overview.
    *   Add a python-based matcher for `EnterPlanMode` that injects the definition floor / schema discovery instructions.
2.  **Enforce Database-Per-Worktree Isolation**:
    Ensure the `task-orchestrator` container is spawned with an isolated database path matching the active worktree (e.g., `~/.local/share/dopemux/worktrees/{worktree_id}/current-tasks.db`). This avoids singleton collisions and enables parallel execution across git worktrees.
3.  **Align ADHD Engine with Schema Progressions**:
    Integrate `get_context(itemId=...)` schema gates directly into the ADHD Engine's attention monitor. When the ADHD Engine detects an active task, it should read the task's required note schema and present a unified, non-bloated "Next Action" focus box that aggregates both ADHD focus and schema gate progress.
4.  **Preserve Proof Finality (AGENTS.md §9)**:
    Retain the strict requirement that `proof-bundle` must be filled before completing any change-producing item, keeping the gate mechanical and deterministic.
