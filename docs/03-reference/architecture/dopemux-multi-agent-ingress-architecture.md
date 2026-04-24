---
id: dopemux-multi-agent-ingress-architecture
title: Dopemux Multi Agent Ingress Architecture
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-22'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Dopemux Multi Agent Ingress Architecture (reference) for dopemux documentation and developer workflows.
---

# Dopemux Multi-Agent Ingress Architecture

## 1. Executive decision

**Final option chosen:** **B. Single Dopemux Agent Gateway / Adaptive Ingress Plane with separate canonical backend authorities**

**Why:**
The weighted evidence converges on one conclusion: Dopemux needs a single, agent-facing ingress/control plane to absorb runtime fragmentation across Claude Code, GitHub Copilot, Gemini CLI, OpenAI Codex, Antigravity, and future runtimes, but it must not absorb canonical truth. Repo truth is explicit that PM authority is split across Leantime, task-orchestrator, ConPort, and dope-memory receipts; memory and retrieval are split across dope-memory, ConPort, and dope-context; and bridges/proxies are not truth owners. The two primary synthesis reports independently recommend the same shape: centralized gateway for auth, routing, MCP aggregation, policy, and event normalization, plus lightweight local shims for runtime-local visibility that a remote gateway cannot see.

**Why not A or C:**
Option **A** leaves the repo in a fragmented agent-integration matrix: too many direct MCP surfaces, too much per-runtime configuration drift, weak centralized policy enforcement, and no clean choke point for auth, logging, or tool filtering across a 30+ service workspace. Option **C** is worse: it would collapse ingress, PM, chronicle, and retrieval into one monolith, directly violating repo-truth boundaries and inheriting unresolved runtime contradictions such as the task-orchestrator launch-path split and other truth gaps. Repo truth and the primary reports both make that collapse unacceptable.

**Plain-language final architecture:**
**Put one adaptive gateway in front of agent runtimes, keep thin local shims at the edge, and leave Leantime, task-orchestrator, ConPort, dope-memory, dope-context, dopetask, and repo-truth-extractor as separate authorities.**

---

## 2. Weighted evidence summary

**What the two primary final reports agree on**

* Vendor extensibility is divergent, not uniform. Claude Code, Copilot, Gemini CLI, and Codex expose different mixes of hooks, MCP, and context injection; Antigravity is materially less deterministic and less well documented.
* The right target is **Option B**: one agent-facing gateway, separate canonical backend authorities.
* **Claude-mem is pattern evidence, not a blueprint.** It proves the need for local capture plus async processing, but its concrete implementation is Claude-specific and not portable as-is.
* The ingress plane should use **event-driven ingestion with async workers**, and only deterministic safety gates should block synchronously.
* Consolidation must be **service-tier-aware**: merge control-plane translation logic, preserve canonical domain authorities, keep local shims separate.

**What the secondary reports add or challenge**

* `Dopemux Agent Architecture Research.md` reinforces Option B and sharpens the “capability-adaptive middle tier” argument.
* `ChatGPT Architecture Report1.md` adds a useful wrapper/listener fallback framing for runtimes that lack first-class hooks. That is useful, but only as a fallback, not as a substitute for gateway + shim discipline.
* `ChatGPT DR report 2.md` broadens the runtime capability comparison and supports the common conclusion that hook/MCP parity does not exist.
* `Dopemux Architecture Research Recommendation.md` adds strong security language and good pressure against direct agent-to-backend access, but it overreaches when it implies centralizing state/memory management in the gateway and when it argues to deprecate wrappers/shims wholesale. Those parts conflict with repo truth and with the primary reports’ gateway-shim split.

**Claims that are weak, provisional, or need re-verification**

* **Antigravity** integration semantics are provisional. The evidence is mixed and lower confidence; treat it as gateway-first and skills/extension-oriented until proven otherwise.
* **Codex** hook behavior is limited enough that full lifecycle interception should not be assumed; benchmark blocking cost before making it critical path.
* **Gemini** exact session/order semantics should be re-verified during implementation. The high-confidence takeaway is simply “hooks + MCP exist, but they are not the same as Claude/Copilot/Codex.”
* Any runtime matrix row that goes beyond official vendor docs should be treated as provisional.

**Repo-truth constraints that dominate the decision**

* `dopemux` is the operator/control surface, not canonical PM, memory, retrieval, or execution truth.
* PM is intentionally split: metadata to **Leantime**, workflow-significant transitions to **task-orchestrator**, structured decisions/progress/context to **ConPort**, mirrored history to **dope-memory**.
* Memory/retrieval are split: **dope-memory** owns chronicle/evidence, **ConPort** owns structured context/decisions/progress/custom data, **dope-context** owns deterministic retrieval/indexing.
* Bridges/adapters/proxies are not authorities.
* The repo is a composed multi-system workspace, not a unified brain.

**External claims explicitly rejected because they conflict with repo truth**

* “Gateway should centralize state/memory management” — **rejected**. Chronicle stays in dope-memory; structured decision/progress/context stays in ConPort.
* “Wrappers/shims should be deprecated in favor of gateway-only integration” — **rejected**. Local runtime visibility is required where the remote gateway cannot observe lifecycle state.
* “Serena should simply be deprecated as duplicate” — **rejected as overbroad**. Repo truth only proves that `serena-v2` is legacy and that Serena runtime authority needs freezing; it does not justify blanket removal of Serena core from this program.

---

## 3. Final architecture

### Gateway responsibilities

**This belongs in the gateway**

* One **agent-facing ingress plane** for:

  * MCP aggregation/facade
  * hook/event intake endpoints
  * auth, identity propagation, policy checks, rate limiting
  * per-runtime capability filtering
  * normalized event emission
  * async dispatch to worker tier
  * operational audit, metrics, and replay-safe ingestion
* A **capability registry** that knows what each runtime can actually do:

  * tools-only MCP vs tools+resources+prompts
  * hookable vs wrapper-only vs watcher-only
  * sync-gate vs async-observation behavior
* A **router/projection layer** that:

  * maps one normalized request/event model to runtime-specific and backend-specific dialects
  * builds deterministic per-agent tool catalogs
  * enforces hidden-surface filtering
  * trims or reshapes context to runtime limits

The gateway owns **control-plane behavior**, not domain truth.

### Local shim responsibilities

**This is a local shim concern**

* Runtime-local lifecycle capture:

  * session start/end
  * prompt submit
  * pre/post tool events
  * local errors
  * local file/process observations that never cross the network otherwise
* Minimal deterministic synchronous gates for dangerous actions only
* Local context injection at the actual runtime hook point when the runtime supports it
* Local spool/ledger for retry when gateway connectivity is degraded
* Version-bound translation from runtime-native events into the canonical event envelope

Local shims are required because the remote gateway cannot observe local state machine transitions directly.

### Adapter types

**Hook adapter**
Maps native lifecycle hooks into the canonical event envelope. Primary for Claude Code, Copilot, Gemini CLI, and limited Codex paths.

**MCP adapter**
Builds the runtime-specific tool catalog and translates backend tool definitions to the runtime’s actual MCP capability set. It must handle tool-only runtimes differently from tools+resources+prompts runtimes.

**Wrapper adapter**
Used when a runtime has insufficient direct hooks but is still automatable as a process/config/extension harness. It can launch, observe, and forward events, but it is still not a truth owner. This is likely relevant for some Codex and no-hook fallback paths.

**Watcher fallback**
Last resort. Passive observation only: stdout/stderr, files, process events, or skill/extension outputs. It must never claim complete lifecycle coverage and must not be trusted for enforcement semantics. Use this for weakly documented or closed runtimes such as Antigravity until stronger evidence exists. **This is provisional and needs verification.**

### Canonical backend responsibilities

**This must remain a separate authority**

* **Leantime** — passive PM metadata and project/ticket snapshot authority
* **task-orchestrator** — workflow-significant transitions and workflow views
* **ConPort** — structured decisions, progress, project context, custom data
* **dope-memory** — chronicle, evidence, replay/recap/reflection/trajectory
* **dope-context** — deterministic indexing/retrieval for code/docs
* **dopetask** — external execution runtime after handoff
* **Repo-Truth-Extractor** — extraction/audit runtime, not operator control

The gateway may route to them, but truth remains with them.

### What the gateway must **not** own

* PM system of record
* Chronicle ledger
* Structured decision/progress/context database
* Retrieval/index source truth
* Execution runtime truth
* Repo-truth extraction truth
* A “unified memory” that collapses dope-memory, ConPort, and dope-context
* Direct DB writes into canonical stores as a shortcut around service APIs

### Interaction model with existing authorities

* Agents talk to **one gateway**
* The gateway talks to canonical systems through **their service interfaces**, not direct DB access
* The gateway may absorb **translation/proxy logic** now living in dopecon-bridge, leantime-bridge, or mcp-client, but only as control-plane middleware and only after parity tests
* Authoritative mutations become true only when the owning service emits/returns success
* Old direct paths stay behind feature flags during migration; they are hidden from agent-visible discovery first, removed later

---

## 4. Canonical event model

### Event envelope

Use the project-required top-level envelope exactly:

```json
{
  "id": "evt_01H...",
  "ts": "2026-04-23T12:34:56Z",
  "workspace_id": "ws_...",
  "instance_id": "inst_...",
  "type": "agent.tool.preflight.observed",
  "source": {
    "system": "shim",
    "component": "claude-code",
    "runtime": "claude-code",
    "host": "local"
  },
  "data": {
    "agent_id": "agent_...",
    "tool": "Bash",
    "payload": {},
    "causation_id": "evt_...",
    "idempotency_key": "evt_01H..."
  }
}
```

The top level stays fixed. Causation, correlation, retry, and routing metadata live inside `data` or `source`, not as extra top-level fields. This keeps the envelope deterministic and aligned with the project event doctrine.

### Normalized event taxonomy

Use three classes only.

**Observations**
Facts observed by shims, gateway, or authorities. No side effect is implied.
Examples:

* `agent.session.started`
* `agent.prompt.submitted`
* `agent.tool.preflight.observed`
* `agent.tool.completed`
* `agent.mcp.requested`
* `gateway.auth.failed`
* `gateway.policy.denied`
* `authority.response.received`
* `runtime.error.observed`

**Actuation**
A control-plane action was taken or requested.
Examples:

* `gateway.route.dispatched`
* `gateway.catalog.projected`
* `shim.block.applied`
* `gateway.context.projection.applied`
* `gateway.rate_limit.enforced`

**Workflow mutations / promoted state events**
These are the only events that represent promoted state changes and must come from the owning authority.
Examples:

* `pm.metadata.updated` → Leantime
* `workflow.transition.committed` → task-orchestrator
* `decision.logged` → ConPort
* `progress.logged` → ConPort
* `chronicle.receipt.recorded` → dope-memory
* `task.outcome.promoted` → owning workflow/execution authority
* `error.recorded` → owning authority or chronicle sink, depending on class

### Required fields

Required every time:

* `id`
* `ts`
* `workspace_id`
* `instance_id`
* `type`
* `source`
* `data`

Missing any field is invalid. The gateway rejects invalid envelopes fail-closed.

### Idempotency strategy

* The **source** generates the event ID once and keeps it stable across retries
* Shims retry with the **same** `id` and `data.idempotency_key`
* Gateway ingress performs insert-if-absent dedupe on `id`
* Downstream authoritative writes must include `source_event_id` or equivalent idempotency key so side effects are deduplicated at the writer, not only at the gateway
* Projection workers track processed IDs and are replay-safe

### Retry behavior

* **Observations:** at-least-once delivery; duplicates are acceptable and suppressed downstream
* **Actuation:** retry only when transport outcome is unknown and the target supports idempotency
* **Workflow mutations:** retry through the owning authority only with stable idempotency keys; never re-materialize mutations from gateway memory alone

### Duplicate suppression

* Gateway dedupe ledger: `event.id`
* Worker dedupe ledger: `event.id`
* Authoritative writer dedupe: `source_event_id`
* Tool/result projection dedupe: `event.id + projected_target`

### Routing destinations by authority slice

* `chronicle.*`, evidence-rich observations, replay-worthy work logs → **dope-memory**
* `decision.*`, `progress.*`, structured project context → **ConPort**
* `workflow.transition.*`, workflow queue/blocker/state mutations → **task-orchestrator**
* `pm.metadata.*`, passive metadata changes → **Leantime**
* `retrieval.*`, index/bootstrap/sync control → **dope-context**
* `support.*` → exposed support services through registry, not canonical truth
* `gateway.*` → gateway operational store only

### Observations vs actuation vs workflow mutation

* **Observation:** “something happened”
* **Actuation:** “gateway/shim tried or blocked something”
* **Workflow mutation:** “an authority committed a state change”

The critical discipline: **the gateway can observe and request; only authorities can commit.**

---

## 5. Service-tier consolidation policy

| service category           | recommended treatment                             | rationale                                                                                                                             | examples from Dopemux                                                                                                                                    |
| -------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| canonical domain authority | **keep separate**                                 | Multiple-writer avoidance. Truth stays with the owning plane/system.                                                                  | Leantime, task-orchestrator, ConPort, dope-memory, dope-context, Repo-Truth-Extractor                                                                    |
| ingress/control            | **merge into gateway**                            | These are control-plane functions with no durable truth. Centralize auth, routing, tool projection, model routing, policy, and audit. | dopemux control-plane logic, LiteLLM-facing model routing                                                                                                |
| support service            | **expose through generated config/registry only** | Useful operational tools, but not canonical truth. They should be agent-visible only through gateway-managed discovery.               | working-memory-assistant, ADHD Engine                                                                                                                    |
| sidecar                    | **keep separate**                                 | Background async jobs should not block the gateway thread or turn the gateway into a sidecar kitchen sink.                            | webhook-receiver, webhook-poller                                                                                                                         |
| adapter/proxy              | **merge into gateway**                            | Translation logic is not authority. Internalize it after parity tests so agents stop seeing proxy sprawl.                             | dopecon-bridge, leantime-bridge, mcp-client; PAL only if it is being used as pure routing/proxy logic                                                    |
| wrapper/shim               | **keep separate**                                 | Local lifecycle visibility is runtime-specific and must stay at the edge.                                                             | Claude/Copilot/Gemini/Codex hook shims, Antigravity skills/extension harness, watcher fallback                                                           |
| duplicate/legacy/drifted   | **deprecate/hide**                                | Unresolved or stale surfaces must disappear from agent-visible discovery first, then be removed after proof.                          | `services/dope-query`, legacy `task_orchestrator/app.py`, `services/adhd-engine` residue, `serena-v2` alias residue, unresolved duplicate exposure paths |

**Important qualification:**
Do **not** blindly deprecate Serena core. Repo truth only supports deprecating stale or duplicate Serena exposure paths until runtime authority is frozen.

---

## 6. Migration plan

### Phase 0 — repo-wide service census + ingress map

**Objective**
Freeze what exists before changing anything.

**What changes**

* Service census by authority, tier, role, merge policy, and agent-visible exposure
* Runtime ingress map for Claude Code, Copilot, Gemini CLI, Codex, Antigravity
* Hidden/deprecated surface inventory
* Direct-agent path inventory

**What remains untouched**

* Canonical services
* Existing PM/memory/retrieval ownership
* Current operator workflows

**Risks**

* Misclassifying bridge/proxy surfaces as authorities
* Missing drifted paths
* Freezing a false runtime target

**Validation gates**

* Every relevant service classified
* Every agent ingress surface mapped
* Every unresolved authority marked `UNKNOWN`
* No Tier 1 authority marked mergeable without proof

**Rollback / containment**

* Docs/registry-only phase; no runtime blast radius

### Phase 1 — canonical event envelope + capability registry

**Objective**
Define the shared control-plane language before building the gateway.

**What changes**

* Event envelope schema
* Event taxonomy
* Per-runtime capability registry
* Idempotency and dedupe contract
* Tool-catalog naming rules

**What remains untouched**

* Routing logic
* Canonical service APIs
* Existing direct paths

**Risks**

* Over-generalized event model
* Leaking truth semantics into ingress semantics

**Validation gates**

* Schema contract tests pass
* Runtime matrix exists for all target runtimes
* Unknowns remain explicit
* No authority boundary weakened

**Rollback / containment**

* Schema/config only

### Phase 2 — local shims + basic gateway ingress

**Objective**
Stand up the minimum viable ingress plane without touching truth ownership.

**What changes**

* Gateway service skeleton
* Authn/authz and rate-limit middleware
* Observation-only ingress endpoints
* Local shims for Claude/Copilot/Gemini/Codex
* Local retry spool contract
* Antigravity provisional adapter spec

**What remains untouched**

* Backend canonical services
* Existing tool routing
* Existing PM/memory/retrieval stores

**Risks**

* Shim drift
* Blocking latency in critical-path hooks
* Gateway SPOF introduced too early

**Validation gates**

* Observation ingest works for each supported runtime
* Duplicate events dedupe correctly
* Gateway outage does not lose local events
* No truth writes originate from gateway

**Rollback / containment**

* Feature-flag off the gateway
* Keep shims in observe-only mode
* Fall back to existing direct paths

### Phase 3 — MCP aggregation / routing layer

**Objective**
Expose one deterministic agent-facing tool catalog.

**What changes**

* Unified MCP surface
* Deterministic namespacing and tool filtering
* Routing to Leantime, task-orchestrator, ConPort, dope-memory, dope-context through owned interfaces
* Incremental internalization of bridge/proxy translation logic

**What remains untouched**

* Canonical data stores
* Ownership boundaries
* dopetask runtime

**Risks**

* Tool-name ambiguity
* Proxy logic accidentally promoted to authority
* Broken routing due to task-orchestrator runtime drift

**Validation gates**

* One catalog per runtime, deterministically ordered
* Ambiguous tool names resolved
* Hidden legacy surfaces absent from discovery
* Task-orchestrator target freeze documented before write-path use

**Rollback / containment**

* Dual-path routing behind feature flag
* Disable gateway catalog projection and restore existing direct config

### Phase 4 — prompt/context injection + async worker model

**Objective**
Add enrichment without making turns slow or letting the gateway own memory.

**What changes**

* Async workers for non-critical processing
* Context projection/budgeting rules
* Deterministic pre-tool synchronous gates
* Chronicle receipt mirroring and enrichment flows
* Capability-adaptive prompt/context shaping

**What remains untouched**

* Canonical memory ownership
* Canonical PM ownership
* Canonical retrieval ownership

**Risks**

* Context bloat
* Reordering bugs
* Event storms
* Hidden memory centralization in the gateway

**Validation gates**

* Token budgets enforced
* Worker replay is idempotent
* Synchronous-only gates are limited to safety-critical checks
* Gateway stores projections/logs, not truth

**Rollback / containment**

* Disable worker consumers
* Leave gateway in pass-through mode
* Fall back to no-injection baseline

### Phase 5 — deprecations, compatibility cleanup, and operator-facing consolidation

**Objective**
Hide drift, reduce operator confusion, and make the new path the default.

**What changes**

* Registry filtering for legacy surfaces
* Cutover docs and operator commands
* Deprecation notices and compatibility shims
* Final direct-agent path removals where parity is proven
* Gateway-first default config generation

**What remains untouched**

* Canonical service boundaries
* External dopetask runtime ownership

**Risks**

* Operator confusion
* Stale configs reintroducing old paths
* Reappearance of hidden legacy surfaces

**Validation gates**

* Deprecated surfaces absent from agent-visible discovery
* Operator smoke tests pass on gateway-first config
* codereview and precommit green
* PR opened with rollback notes and route map

**Rollback / containment**

* Re-enable old config generation
* Re-open old direct paths temporarily
* Keep gateway present but non-default

**First safe implementation slice:**
**Phase 1** is the first safe slice. It gives you the event schema and capability registry without changing runtime ownership or traffic. That is where this should start.

---

## 7. ADR

**Title**
Adopt a Dopemux Adaptive Ingress Plane with local runtime shims and separate canonical authorities

**Status**
Accepted as the target architecture

**Context**
Dopemux is a service-dense workspace with split authority across PM, chronicle, structured context, retrieval, and execution. Agent runtimes expose divergent hook/MCP surfaces, so direct point-to-point integration does not scale. Repo truth forbids collapsing adapters, memory, retrieval, and PM truth into one monolith.

**Decision**
Implement one agent-facing gateway for ingress/control concerns only. Keep local runtime shims for lifecycle visibility that the gateway cannot observe remotely. Preserve Leantime, task-orchestrator, ConPort, dope-memory, dope-context, dopetask, and Repo-Truth-Extractor as separate authorities. Route all authoritative mutations through owned service interfaces. Use a canonical event envelope, capability registry, deterministic tool catalogs, async workers for non-critical processing, and feature-flagged migration.

**Consequences**

* Positive: one policy/auth/audit choke point; easier runtime onboarding; cleaner agent-visible surface
* Negative: new gateway SPOF; shim maintenance burden; extra hop; contract-testing burden
* Constraint: the gateway may centralize ingress logic, but it may not centralize truth

**Rejected alternatives**

* **A**: direct multi-server integration with better hooks only — too fragmented
* **C**: monolithic Dopemux owning ingress and backend truth — boundary violation

---

## 8. Codex-ready task packet series

The series below follows the strict packet contract shape and uses a Codex PAL chain of `analyze -> planner -> codereview -> precommit`.

```json
{
  "id": "TP-DMX-AIG-001",
  "project": "dopemux",
  "target": "repo-wide service census and ingress map",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Do not change canonical writers.",
    "Do not normalize drift away.",
    "Mark unresolved authority as UNKNOWN."
  ],
  "depends_on": [],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-001-census"
  },
  "commit": {
    "message": "docs(architecture): add multi-agent service census and ingress map",
    "allowlist": [
      "docs/03-reference/architecture/multi-agent-service-census.md",
      "docs/03-reference/architecture/multi-agent-ingress-map.md",
      "tests/architecture/test_multi_agent_census.py"
    ],
    "verify": [
      "pytest tests/architecture/test_multi_agent_census.py"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-001] Add multi-agent service census and ingress map",
    "body": "Adds repo-truth service classification and runtime ingress mapping for the multi-agent ingress program.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Create a repo-wide census that classifies each relevant service by tier, role, authority slice, and merge policy.",
      "requirements": [
        "Use runtime code, compose wiring, service registry, and truth docs only.",
        "Separate canonical authority from adapter or proxy exposure.",
        "Do not declare new authority."
      ],
      "commands": [
        "rg -n \"services/|src/dopemux|docker/mcp-servers-source\" docs services src compose.yml docker/compose.core.yml services/registry.yaml",
        "pytest tests/architecture/test_multi_agent_census.py"
      ],
      "expected_files": [
        "docs/03-reference/architecture/multi-agent-service-census.md"
      ],
      "validation": [
        "Every service in scope is classified.",
        "No Tier 1 authority is marked mergeable without proof."
      ]
    },
    {
      "id": "S2",
      "task": "Create an ingress map for Claude Code, GitHub Copilot, Gemini CLI, OpenAI Codex, Antigravity, and future-runtime placeholders.",
      "requirements": [
        "List hook, MCP, wrapper, and watcher surfaces separately.",
        "Mark provisional integrations explicitly."
      ],
      "commands": [
        "pytest tests/architecture/test_multi_agent_census.py"
      ],
      "expected_files": [
        "docs/03-reference/architecture/multi-agent-ingress-map.md"
      ],
      "validation": [
        "Every target runtime has a mapped ingress path.",
        "Unknown or weakly documented paths are marked provisional."
      ]
    }
  ]
}
```

```json
{
  "id": "TP-DMX-AIG-002",
  "project": "dopemux",
  "target": "canonical event envelope and runtime capability registry",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Keep the top-level event envelope fixed to id, ts, workspace_id, instance_id, type, source, data.",
    "Do not move truth into ingress."
  ],
  "depends_on": [
    "TP-DMX-AIG-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-AIG-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-002-events"
  },
  "commit": {
    "message": "feat(agent-gateway): define ingress event schema and runtime capability registry",
    "allowlist": [
      "services/dopemux-agent-gateway/contracts/ingress_event.schema.json",
      "services/dopemux-agent-gateway/config/runtime_capabilities.yaml",
      "docs/03-reference/architecture/multi-agent-event-model.md",
      "tests/agent_gateway/test_ingress_event_schema.py"
    ],
    "verify": [
      "pytest tests/agent_gateway/test_ingress_event_schema.py"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-002] Define ingress event schema and capability registry",
    "body": "Adds the canonical ingress envelope, taxonomy, idempotency contract, and runtime capability registry.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Add the canonical ingress event schema and normalized taxonomy.",
      "requirements": [
        "Keep the top-level envelope exact.",
        "Separate observations, actuation, and workflow mutations.",
        "Define idempotency and dedupe rules."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_ingress_event_schema.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/contracts/ingress_event.schema.json",
        "docs/03-reference/architecture/multi-agent-event-model.md"
      ],
      "validation": [
        "Schema rejects missing required top-level fields.",
        "Taxonomy does not assign truth ownership to the gateway."
      ]
    },
    {
      "id": "S2",
      "task": "Add the runtime capability registry used by adapters and tool-catalog projection.",
      "requirements": [
        "List supported MCP scope, hook model, fallback mode, and provisional status per runtime.",
        "Keep unknowns explicit."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_ingress_event_schema.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/config/runtime_capabilities.yaml"
      ],
      "validation": [
        "All target runtimes are present.",
        "Capability differences are represented without false parity."
      ]
    }
  ]
}
```

```json
{
  "id": "TP-DMX-AIG-003",
  "project": "dopemux",
  "target": "gateway skeleton and local shim contract",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Observation ingest first; no authoritative writes from the gateway.",
    "Shims must be replay-safe."
  ],
  "depends_on": [
    "TP-DMX-AIG-002"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-AIG-002",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-003-skeleton"
  },
  "commit": {
    "message": "feat(agent-gateway): add gateway skeleton and shim replay contract",
    "allowlist": [
      "services/dopemux-agent-gateway/app/main.py",
      "services/dopemux-agent-gateway/app/auth.py",
      "services/dopemux-agent-gateway/app/dedupe.py",
      "services/dopemux-agent-gateway/app/routes_ingest.py",
      "configs/agent-shims/README.md",
      "tests/agent_gateway/test_ingest_replay.py"
    ],
    "verify": [
      "pytest tests/agent_gateway/test_ingest_replay.py"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-003] Add gateway skeleton and shim replay contract",
    "body": "Introduces the minimal gateway runtime, replay-safe ingest, and shim contract documentation.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Create the minimal gateway runtime with health, auth middleware, ingress routes, and dedupe storage.",
      "requirements": [
        "Accept only canonical ingress envelopes.",
        "Store operational ingest state only.",
        "Return deterministic duplicate acknowledgements."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_ingest_replay.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/app/main.py",
        "services/dopemux-agent-gateway/app/routes_ingest.py",
        "services/dopemux-agent-gateway/app/dedupe.py"
      ],
      "validation": [
        "Duplicate events do not create duplicate side effects.",
        "Invalid envelopes fail closed."
      ]
    },
    {
      "id": "S2",
      "task": "Define the local shim contract and spool behavior for supported runtimes.",
      "requirements": [
        "Document stable event ids across retries.",
        "Separate hook adapters from wrapper or watcher fallbacks."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_ingest_replay.py"
      ],
      "expected_files": [
        "configs/agent-shims/README.md"
      ],
      "validation": [
        "Shim contract includes retry, dedupe, and failure-mode behavior.",
        "No shim claims canonical truth ownership."
      ]
    }
  ]
}
```

```json
{
  "id": "TP-DMX-AIG-004",
  "project": "dopemux",
  "target": "local shims for supported runtimes and watcher fallback contract",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Only deterministic safety gates may block synchronously.",
    "Watcher fallback is observation-only."
  ],
  "depends_on": [
    "TP-DMX-AIG-003"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-AIG-003",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-004-shims"
  },
  "commit": {
    "message": "feat(agent-gateway): add runtime shims and fallback watcher contract",
    "allowlist": [
      "configs/agent-shims/claude/",
      "configs/agent-shims/copilot/",
      "configs/agent-shims/gemini/",
      "configs/agent-shims/codex/",
      "docs/03-reference/architecture/antigravity-provisional-adapter.md",
      "tests/agent_gateway/test_runtime_shim_contracts.py"
    ],
    "verify": [
      "pytest tests/agent_gateway/test_runtime_shim_contracts.py"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-004] Add runtime shims and fallback watcher contract",
    "body": "Adds concrete shim configs for supported runtimes and a provisional fallback spec for weakly documented runtimes.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Add shim configs or scripts for Claude Code, GitHub Copilot, Gemini CLI, and OpenAI Codex.",
      "requirements": [
        "Map runtime-native hook points to the canonical ingress schema.",
        "Limit synchronous blocking to explicit safety gates."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_runtime_shim_contracts.py"
      ],
      "expected_files": [
        "configs/agent-shims/claude/",
        "configs/agent-shims/copilot/",
        "configs/agent-shims/gemini/",
        "configs/agent-shims/codex/"
      ],
      "validation": [
        "Each supported runtime has a concrete shim path.",
        "Each shim preserves stable event ids across retries."
      ]
    },
    {
      "id": "S2",
      "task": "Add the watcher fallback and Antigravity provisional integration contract.",
      "requirements": [
        "Mark it as observation-only.",
        "Do not claim full lifecycle coverage."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_runtime_shim_contracts.py"
      ],
      "expected_files": [
        "docs/03-reference/architecture/antigravity-provisional-adapter.md"
      ],
      "validation": [
        "Fallback semantics are explicitly degraded.",
        "No critical-path safety assumptions depend on watcher coverage."
      ]
    }
  ]
}
```

```json
{
  "id": "TP-DMX-AIG-005",
  "project": "dopemux",
  "target": "MCP aggregation, deterministic routing, and authority-safe adapters",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Route only through owned service interfaces.",
    "Do not expose hidden legacy surfaces in tool discovery."
  ],
  "depends_on": [
    "TP-DMX-AIG-004"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-AIG-004",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-005-routing"
  },
  "commit": {
    "message": "feat(agent-gateway): add MCP aggregation and authority-safe routing",
    "allowlist": [
      "services/dopemux-agent-gateway/app/catalog.py",
      "services/dopemux-agent-gateway/app/router.py",
      "services/dopemux-agent-gateway/app/adapters/",
      "services/dopemux-agent-gateway/config/tool_visibility.yaml",
      "tests/agent_gateway/test_catalog_routing.py"
    ],
    "verify": [
      "pytest tests/agent_gateway/test_catalog_routing.py"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-005] Add MCP aggregation and authority-safe routing",
    "body": "Adds one deterministic agent-facing catalog, authority-safe routing, and hidden-surface filtering.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Implement the deterministic tool catalog and per-runtime filtering rules.",
      "requirements": [
        "Names must be stable and collision-safe.",
        "Tool visibility must be generated from the registry, not hand-edited per runtime."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_catalog_routing.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/app/catalog.py",
        "services/dopemux-agent-gateway/config/tool_visibility.yaml"
      ],
      "validation": [
        "Catalog order is deterministic.",
        "Hidden or drifted surfaces are absent from discovery."
      ]
    },
    {
      "id": "S2",
      "task": "Implement authority-safe routing adapters for Leantime, task-orchestrator, ConPort, dope-memory, and dope-context.",
      "requirements": [
        "Use service APIs or MCP surfaces only.",
        "Do not route through direct DB access.",
        "Keep writes on the owning authority."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_catalog_routing.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/app/router.py",
        "services/dopemux-agent-gateway/app/adapters/"
      ],
      "validation": [
        "Each routed mutation targets the correct authority.",
        "Bridge logic, if internalized, stays middleware-only."
      ]
    }
  ]
}
```

```json
{
  "id": "TP-DMX-AIG-006",
  "project": "dopemux",
  "target": "async workers, prompt projection, cutover flags, deprecations, and final hardening",
  "invariants": [
    "Use a fresh worktree and scoped branch.",
    "Async enrichment must not become canonical truth.",
    "Completion requires codereview, precommit, push, and PR."
  ],
  "depends_on": [
    "TP-DMX-AIG-005"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-AIG-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-AIG-005",
    "final_packet": true
  },
  "execution": {
    "agent": "codex",
    "branch": "tp/dmx-aig-006-cutover"
  },
  "commit": {
    "message": "feat(agent-gateway): add async workers, cutover flags, and final deprecations",
    "allowlist": [
      "services/dopemux-agent-gateway/app/workers.py",
      "services/dopemux-agent-gateway/app/context_projection.py",
      "services/dopemux-agent-gateway/config/feature_flags.yaml",
      "docs/03-reference/architecture/multi-agent-cutover-runbook.md",
      "tests/agent_gateway/test_cutover_and_replay.py"
    ],
    "verify": [
      "pytest tests/agent_gateway/test_cutover_and_replay.py",
      "pre-commit run --all-files"
    ]
  },
  "pr": {
    "title": "[DMX-AIG-006] Add worker tier, cutover flags, and final hardening",
    "body": "Completes the first safe gateway cutover with async workers, feature flags, hidden-surface cleanup, codereview, precommit, and PR proof.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Add async workers, context projection budgets, and replay-safe enrichment.",
      "requirements": [
        "Only deterministic safety checks may stay synchronous.",
        "Context projection must be bounded and runtime-aware."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_cutover_and_replay.py"
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/app/workers.py",
        "services/dopemux-agent-gateway/app/context_projection.py"
      ],
      "validation": [
        "Replay is idempotent.",
        "Gateway stores projections and operational state only."
      ]
    },
    {
      "id": "S2",
      "task": "Add feature-flagged cutover, hide legacy surfaces, run codereview, run precommit, push branch, and open the PR.",
      "requirements": [
        "Do not remove old paths until parity is proven.",
        "Record rollback notes and route maps in the PR."
      ],
      "commands": [
        "pytest tests/agent_gateway/test_cutover_and_replay.py",
        "pre-commit run --all-files",
        "git push -u origin tp/dmx-aig-006-cutover",
        "gh pr create --base main --head tp/dmx-aig-006-cutover --title \"[DMX-AIG-006] Add worker tier, cutover flags, and final hardening\""
      ],
      "expected_files": [
        "services/dopemux-agent-gateway/config/feature_flags.yaml",
        "docs/03-reference/architecture/multi-agent-cutover-runbook.md"
      ],
      "validation": [
        "codereview findings are resolved or explicitly accepted with rationale.",
        "precommit passes.",
        "Branch is pushed.",
        "PR is opened and its URL is recorded in the packet proof."
      ]
    }
  ]
}
```

---

## 9. Failure modes and mitigations

**Gateway becomes fake authority**
Mitigation: no direct DB writes, no shared truth DB, no mutation considered committed until emitted by the owning authority, and contract tests that trace every write path back to Leantime, task-orchestrator, ConPort, dope-memory, or dope-context as appropriate.

**Local shims drift from vendor runtimes**
Mitigation: capability registry includes supported versions, shims get contract tests and release-candidate smoke tests, and shim failures degrade to observation-only rather than silently claiming enforcement.

**MCP aggregation hides dangerous ambiguity**
Mitigation: deterministic tool names, per-runtime catalog filtering, explicit source metadata in responses, and CI that blocks duplicate unresolved tool names.

**Event duplication / replay bugs**
Mitigation: stable event IDs from source, gateway dedupe on `id`, downstream idempotency on `source_event_id`, replay tests before cutover.

**Auth / identity propagation failure**
Mitigation: gateway is the only ingress choke point, every routed request carries workspace/instance identity, unknown identities fail closed, and auth decisions are auditable.

**Prompt/context injection bloat**
Mitigation: projection budgets, deterministic truncation/summarization rules, per-runtime context classes, and async workers for non-critical enrichment.

**Antigravity / weakly documented runtime mismatch**
Mitigation: keep Antigravity in provisional status, use gateway-first MCP/skill integration if available, treat watcher fallback as observation-only, and do not make it a critical-path runtime until verified.

**Migration confusion between old and new paths**
Mitigation: feature flags, side-by-side catalogs, explicit cutover runbook, operator-visible route maps, and reversible config generation.

**Stale legacy services reappearing as agent-visible surfaces**
Mitigation: generated registry only, denylist for drifted paths, CI that fails if deprecated surfaces re-enter discovery, and final hide-before-delete discipline.

**Single point of failure / performance regression**
Mitigation: HA deployment, rate limits, local shim spooling, pass-through fallback mode, and strict rule that only safety gates block synchronously.

---

## 10. Open questions

Only the real ones:

1. **Antigravity** — what exact programmable surface is stable enough for supported integration: MCP, skills, extension, or only passive observation?
2. **Codex** — what blocking latency budget is acceptable for shim-to-gateway calls on real workloads, given limited hook interception?
3. **Gemini** — what exact ordering and session semantics should be frozen in the normalized taxonomy?
4. **task-orchestrator** — which deployable runtime/port is the canonical backend target for gateway write-path routing: `app/main.py` on 3014, or compose/registry exposure on 8000?
5. **Serena exposure** — which Serena runtime path is canonical enough to be agent-visible, and which duplicate paths must be hidden first?
