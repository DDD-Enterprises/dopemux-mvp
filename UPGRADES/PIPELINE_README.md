# Phase D: Docs Pipeline Overview

Run Phase D (Docs P0–P5) after you’ve captured the control plane surfaces (repo + home), and before any deep arbitration/synthesis (5.2 / Opus). That order prevents two classic failure modes:
- You miss “magic” encoded in instruction/config files and misread the architecture.
- You let old archive docs dominate your mental model before you’ve extracted supersession/recency.

## Model choice for Phase D

*   **Gemini Flash 3**: D0–D5 (best default)
*   **Grok-code-fast-1**: only if Flash fails to keep strict JSON-only, or if you want faster extraction of large code-fenced docs, but still riskier for “helpful” drift

## Minimal “today” run set (if time is tight)

Do these in order:
1.  **D0**
2.  **D1** on `P2_CORE_ARCH__*`, `P3_PLANES_ACTIVE__*`, `P5_TASK_PACKETS_PM_INV__*`
3.  **D2** on those same partitions
4.  **D4**
5.  **D5**

That gives you architecture, planes, workflows, and decision spine without archive bloat.

## Full pipeline order (recommended)

### Phase A: Repo control plane scan (Tier 0)

*   **Model**: Gemini Flash 3
*   **Inputs**: repo working tree
*   **Outputs**: instruction/config surfaces (MCP, routers, hooks, compose, litellm configs, custom-instructions)

*Why first: this is the runtime steering wheel.*

### Phase H: Home control plane scan (Tier 0, your ~/.dopemux + ~/.config/dopemux)

*   **Model**: Gemini Flash 3
*   **Outputs**: HOME_* JSONs (H1–H4)

*Why second: reveals local-only enablement and truth splits.*

### Phase D: Docs extraction pipeline (P0–P5)

*   **Model**: Gemini Flash 3
*   **Outputs**: doc inventory, claims/boundaries/supersession, deep interfaces/workflows, merge+QA, clusters

*Why here: now you can read docs with the control plane context, and your doc clustering won’t get hijacked by archive noise because supersession + flags are extracted early.*

### Phase C: Code surfaces (only if needed)

*   **Model**: Grok-code-fast-1 (optional)
*   **Use only if**: your existing *_SURFACE.json artifacts are stale or incomplete.

*Why after docs: docs tell you what code surfaces actually matter, so you can limit code scanning to the relevant subsystems (Dope-Memory, EventBus, TaskX integration points).*

### Phase R: Arbitration (Truth maps + conflict ledger)

*   **Model**: GPT-5.2 Extended Thinking
*   **Inputs**: HOME surfaces + repo control plane surfaces + merged doc artifacts + (optional) code surfaces
*   **Outputs**:
    *   CONTROL_PLANE_TRUTH_MAP.md
    *   WORKFLOW_TRUTH_GRAPH.md
    *   TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
    *   DOPE_MEMORY_IMPLEMENTATION_TRUTH.md
    *   EVENTBUS_WIRING_TRUTH.md
    *   TASKX_INTEGRATION_TRUTH.md
    *   PORTABILITY_RISK_LEDGER.md

*Why here: this is where “what’s true” is decided, using extracted evidence only.*

### Phase S: Synthesis (2 Opus runs)

*   **Model**: Opus
    *   Opus #1: architecture + subsystem boundaries + workflows (from truth maps + clusters)
    *   Opus #2: MCP → hooks migration impact + new dataflow shape plan (from control plane + portability risks + workflows)

*Why last: Opus should synthesize, not excavate.*

## The quick “today” sequence (minimum to unblock architecture)

If you only do a few steps today:
1.  **H2** (home MCP/router/litellm/hooks surface)
2.  **D0** (docs inventory + partitions)
3.  **D1+D2** for `P2_CORE_ARCH` + `P3_PLANES_ACTIVE` + `P5_TASK_PACKETS_PM_INV`
4.  **D4+D5** (merge + clusters)
5.  **5.2 arbitration truth pack**
6.  **Opus #1** (and #2 if time)

## One strict rule for correctness

Do not run 5.2 arbitration until D4 merge + QA is done.
Otherwise you’ll get a false sense of completion while some partitions never got extracted.
