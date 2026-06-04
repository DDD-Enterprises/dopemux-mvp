# DCP 5.5 Synthesis Input Pack

> [!NOTE]
> **Provenance**: `EXTERNAL_PROPOSED`  
> **Status**: Preservation Only (Design Input / Non-Runtime)

**Packet**: TP-DCP-COMPRESS-0001 (Stage 2 assembly)
**Assembler**: Opus (max thinking), 2026-06-03
**Worktree**: `/Users/hue/code/dopemux-mvp-wt-dcp-evidence` (branch `dcp/evidence-campaign`)
**Inputs**: D1–D5 section drafts (`synthesis/_drafts/`); `TASK_ORCHESTRATOR_BOUNDARY_DECISION.md`; `CAMPAIGN_PROGRESS.md`; `DCP_CAMPAIGN_SPEC_v2.md`; `DCP_DR_EXTERNAL_CONSTRAINTS_LEDGER.md`.

> **THIS PACK IS INPUT TO SYNTHESIS, NOT THE ARCHITECTURE DECISION.** It compresses ~21 read-only evidence packets + a 16-report DR ledger for a GPT-5.5 architecture synthesis. It does not decide where DCP Core lives, what gets built, or in what order. It frames the evidence, the options, the unknowns, and the decisions GPT-5.5 must make.

> **AUTHORITY DISCIPLINE (load-bearing).** Repo runtime evidence (the `evidence/*.md` packets) **OUTRANKS** external DR reports. Corroboration by a DR report raises confidence in a repo finding; it never promotes the DR finding to runtime rank. Open PRs and generated TP series are **CLAIMED_ONLY** (design intent, not landed authority). Contradictions are **preserved, not resolved** — where a source packet resolved one, its resolution label is carried verbatim, but genuinely-open cross-packet contradictions are kept open. UNKNOWN is never upgraded to fact.

> **Authority-order for synthesis** (from BOUNDARY §9, generalized): latest user instruction > `AGENTS.md` / campaign spec > runtime code (store.py, main.py, wrappers) > schemas/interfaces > tests/fixtures > config/CI > docs/comments > external DR (VENDOR_DOCS) > assumptions.

---

## 1. Executive Evidence Summary

The read-only DCP evidence campaign produced ~21 runtime-evidence packets plus a 16-report external DR ledger. The dominant findings, each load-bearing for the architecture synthesis:

1. **"Task Orchestrator" is four distinct surfaces, not one** (BOUNDARY; D1 §3; CURRENT-0001). The shared `.mcp.json` key / `compose.yml` service name `task-orchestrator` is the origin of all prior campaign confusion. The four surfaces — jpicklyk v3.8.0 MCP (S1), stale Kotlin clone (S2), Dopemux FastAPI coordination service (S3), Dopetask executor (S4) — plus a fifth DCP-adjacent auditor module (S5, `src/dopemux/orchestrator/`) have different products, state backends, transports, and ownership domains. Conflating any two is FORBIDDEN by the boundary memo.

2. **DCP Core is the evidence/readiness/proof/action-planning authority; it is none of the four TO surfaces** (BOUNDARY THE DECISION; spec §2). It reads from all surfaces and writes to none until `LIVE_WRITE_READY` is explicitly proven. `LIVE_WRITE_READY` is **UNDEFINED anywhere in the codebase** (`rg` → zero results, TP-0004) — the master gate condition for any live TO write does not yet exist as code, flag, or contract.

3. **The proof surface is fragmented: 5 structurally-incompatible PROOF.json shape families coexist** (D2 §5.1; PROOF-0001). There is no single unified proof contract. DCP must implement shape-family dispatch, pointer-first, with `auditorVerdict` kept distinct from `validationState` (D5 GATE-EXT-4). The only generic cross-system proof pointer observed is the dNh RDCP `PROOF_POINTER.json` (a prior-campaign artifact).

4. **The autoreview / PR-Steward / Action-Bridge / audit surface is real but split into opposite mutation postures** (D2 §6; D4 §1.3). `tools/pr_steward/` + `tools/pr_action_bridge/compiler.py` are ZERO-mutation by schema const-enforcement; `src/dopemux_pr_merge_specialist/` (60+ modules) is a SEPARATE mutation-capable plane with live `gh pr merge execute=True` and a designed-but-ABSENT `steward_gate.py`. The largest in-flight surface (DMX-AUTOREVIEW-PLATFORM + the merge specialist) is entirely CLAIMED_ONLY.

5. **Branch protection on main is ACTIVE with 8 required checks, strict mode** (D2 §6.4; GITHUB-0001). The Gemini automation lane is production-integrated (not experimental), credential-gated, with real `contents: write` capability. GitHub is the merge authority; DCP must not become one.

6. **Memory/Context/Chronicle is a split-authority family where no system is a general/PM/cross-system authority** (D3 §8; MEMCTX-0001). Each of ConPort / dope-memory(chronicle) / dope-context / dopecon-bridge / working-memory-assistant is AUTHORITY only for its own narrow slice. DCP v1 posture = READ/EXPORT/POINTER only across all five. Two systems present CONFLICTING runtime surfaces (ConPort 3004-vs-memory_server; dope-memory 3020-vs-8096).

7. **The cockpit is NOT greenfield — it is a multi-layer system at different maturities** (D4 §8; COCKPIT-0001). A governed TUI PM slice is merged to main and guarded (static demo, no live writes); a newer cockpit wave is on a feature branch only; implementer mode is not built; all TP design-gating still carries `safe_for_claude_design: "NO"`. Six dashboard surfaces exist; only one is DCP-governed.

8. **Tooling infrastructure exists at scale but with UNKNOWN integration mechanisms** (D4 Tooling subsection; TOOLING-0001). 10 lifecycle hooks, 12 pre-commit guards, 80 personas, 20 skill templates, 27 commands, 60+ validators — deterministic infra is real, not aspirational. Persona-routing, skill-instantiation, and MCP-config currency are UNKNOWN; the Sequential→PAL MCP migration is incomplete per config evidence.

9. **External DR (16 reports) corroborates the repo's projection-first posture and constrains the design space** (D5 §9–§10). All DR is `VENDOR_DOCS / LOWER_THAN_REPO_RUNTIME`. The 10 external-constraint gates (§9 below) define the *walls* of the problem space; they are not confirmed doors in the implementation. DR-013 ran fail-closed (no repo) and confirmed no pre-synthesis contradiction ledger was produced externally.

10. **Dopemux and dNh_CRM are fundamentally asymmetric** (D3 §9; XPROJ-0001). dNh is event-sourced with a file-path-anchored red-lane classifier (11 confirmed lanes + 1 probable); Dopemux is split-authority with governance-level-only red lanes (no runtime classifier). A cross-project adapter must preserve this asymmetry — do not fake symmetry.

---

## 2. Authority Map

Every observed surface, with classification, DCP posture, and key unknowns. Merged from all four code-facing drafters (D1 TO/Dopetask; D2 proof/PR; D3 memory/red-lane; D4 cockpit/tooling). **CONFLICTING runtime flags are preserved** — DCP must not flatten them. Authority-tier vocabulary follows spec §6 (`WORK_GRAPH_SURFACE`, `COORDINATION_SERVICE`, `PRODUCT_SOURCE`, `REFERENCE_ONLY`, `CLAIMED_INTENT`, etc.).

### 2.1 Task Orchestrator family (the four surfaces + S5)

| Surface | Classification | DCP Posture | Owns Durable State? | Key Unknowns |
|---|---|---|---|---|
| **DCP Core** | AUTHORITY | Owner; reads all surfaces; writes to none until LIVE_WRITE_READY proven | YES — proof bundles, evidence artifacts | Not yet built; this campaign defines it (BOUNDARY §4) |
| **S1: jpicklyk v3.8.0 MCP Docker** | WORK_GRAPH_SURFACE | DRY-RUN PROJECTION ONLY — read tools only until LIVE_WRITE_READY proven | YES — SQLite `~/.local/share/dopemux-mission-control/task-orchestrator/<wsid>/current-tasks.db` (active dir `2e346e20`, 3.9MB, 262 work_items) | Canonical workspace dir ambiguous across 7 split dirs; proof-envelope gap; schema-free mode active; Flyway runs every container start (D1 §3.1) |
| **S2: Kotlin clone** (`/Users/hue/code/task-orchestrator`) | PRODUCT_SOURCE / REFERENCE_ONLY | Contract archaeology only; VENDOR_DOCS freshness | NO — not a runtime | Last commit 2026-03-20, v2.2.0 pre-v3; schema drift from live v3.8.0 UNKNOWN (D1 §3.1) |
| **S3: Dopemux FastAPI** (`services/task-orchestrator`, "Dopemux Plane Coordination API") | COORDINATION_SERVICE | FUTURE COCKPIT / COORDINATION BRIDGE — do NOT treat as TO authority | PARTIAL — in-memory for execution/PM (volatile); ConPort custom_data for workflow_ideas/epics only via DopeconBridge | S3→S1 `server.py` subprocess spawn coupling OPEN_PENDING; SSE wiring UNKNOWN; **NO auth middleware on any route (VERIFIED)**; fire-and-forget ConPort sync lossy (D1 §3.1) |
| **S4: Dopetask** (`scripts/dopetask` + `scripts/taskx`) | EXECUTOR / PROOF_LIFECYCLE_ADAPTER | KEEP SEPARATE — campaign FORBIDS invocation; adapter-layer read-only consumption only | YES — series state `out/tp_series/<id>/SERIES_STATE.json` (repo-local, ephemeral; dir ABSENT) | v0.5.1 pinned; FlightDeckOpsEngine internal mutation depth UNKNOWN (D1 §4) |
| **S5: `src/dopemux/orchestrator/`** | AUDITOR / DCP-Core-adjacent | DCP-Core-adjacent — `validation/proof.py` + `policy.py` directly relevant to DCP proof contracts | NO — policy YAML-driven, validation in-process | Policy tiers T0–TX exist in code but NOT enforced in live S3 routes (VERIFIED) (D1 §3.1, BOUNDARY §4) |

**jpicklyk dual-truth (carried, not collapsed):** S1 IS authoritative for its own internal task graph (Owns-state = YES); FROM DCP's perspective it is a projection target. Both true at different scopes (BOUNDARY §8 row 3; C-D1-03).

### 2.2 Memory / Context / Chronicle adapter family (MEMCTX-0001; D3 §8)

**No system is a general/cross-system/PM authority. Each owns one narrow slice. DCP v1 = READ/EXPORT/POINTER only across all five.**

| System | Authority Slice (Owns) | Does NOT Own | Runtime Status | Tier | DCP Use |
|---|---|---|---|---|---|
| **ConPort** | Decisions, progress, workspace context, custom-data, relationship traversal/query | PM metadata, workflow legality, chronicle, retrieval, **relationship WRITE (UNKNOWN — no write API proven)** | **CONFLICTING**: `enhanced_server.py` (docker, 3004) vs `src/conport/memory_server.py` — deployed primary UNRESOLVED | AUTHORITY (CONFLICTING) | READ via port 3004 |
| **dope-memory / chronicle** | SQLite chronicle ledger (`work_log_entries`, `raw_activity_events`, `issue_links`, `reflection_cards`); recap/replay/correction/reflection/trajectory | ConPort structured memory, retrieval, PM metadata | **CONFLICTING**: `dope_memory_main.py` port 3020 (active) vs `mcp_stdio_adapter.py` legacy 8096 (stale — do NOT use) | AUTHORITY (CONFLICTING) | READ via 3020 only |
| **dope-context** | Code/docs retrieval + index behavior (Qdrant + BM25); retrieved material stays owned upstream | PM authority, chronicle, ConPort authority | OBSERVED: `services/dope-context/src/mcp/server.py` (FastMCP) | AUTHORITY (OBSERVED, narrow) | READ `search_code()`/`docs_search()`/`search_all()` via 3010 |
| **dopecon-bridge** | Adapter/proxy/event-transport only: `/route/pm`, `/kg/*` (ConPort proxy), `/ddg/*` | **ANY decision/workflow/progress/PM/chronicle/retrieval authority — never canonical writer** | TRANSPORT_ONLY: `routes.py` header + manifest both confirm | ADAPTER (TRANSPORT_ONLY) | READ only; never treat bridge-proxied payload as bridge truth |
| **working-memory-assistant** | Snapshot/recovery/ADHD-support service; co-located with dope-memory but NOT chronicle canonical runtime | Chronicle authority, ConPort authority | UNKNOWN: manifest status UNKNOWN; does not control 3020 | UNKNOWN | No DCP v1 use |

**Bridge overclaim (preserved, MEMCTX §8 C2):** `dopecon_bridge_client/README.md:7` claims bridge is "single authority point" for ConPort/KG — CONTRADICTS `routes.py` header (TRANSPORT_ONLY) and `runtime_authority_manifest.json`. Runtime + manifest override; README is doc drift. DCP must not inherit this claim.

**PM four-way split (PM_PLANE.md; `src/dopemux/pm/writes.py` runtime-enforces routing):** PM metadata → **Leantime**; workflow transitions/legality/blockers → **task-orchestrator**; structured decisions/progress/context → **ConPort**; chronicle/receipts/replay → **dope-memory**; retrieval → **dope-context**; routing → **dopecon-bridge** (never canonical writer).

### 2.3 Proof / PR / GitHub surfaces (D2)

| Surface | Classification | Mutation Posture | Tier | Notes |
|---|---|---|---|---|
| `tools/pr_steward/` (collector, classifier, intake) | ADVISORY CHECK | ZERO — `mutation_performed` schema `const false` (5 schemas) | AUTHORITY (OBSERVED + VERIFIED_BY_PROOF) | GHA read-only perms; `continue-on-error: true` (not a blocking check) |
| `tools/pr_action_bridge/compiler.py` | PURE FUNCTION | ZERO — no subprocess/gh/FS I/O; `mutation_performed` `const false` | AUTHORITY (VERIFIED_BY_PROOF) | No production callers (tests only); awaiting TP-102 CLI (ABSENT) |
| `src/dopemux_pr_merge_specialist/` (63 .py) | RUNTIME_SERVICE_PLANE | **MUTATION-CAPABLE** — `queue_drain.py:2017` `gh pr merge --auto execute=True`; `gh pr ready` | AUTHORITY (OBSERVED, LIVE) | `steward_gate.py` (designed fail-closed guard) **FILE DOES NOT EXIST**; merge seam UNGUARDED |
| `scripts/batch_resolve_and_merge.py` | OPERATOR SCRIPT | **MUTATION** — `resolveReviewThread` + `gh pr merge --squash` | AUTHORITY (OBSERVED) | NOT connected to compiler.py; must NEVER be called from DCP automation; no guardrail |
| `tools/auditor_router/` (5 py) | STATIC CLASSIFIER | ZERO — no subprocess/CLI invocation | AUTHORITY (OBSERVED) | Produces `AUDITOR_ROUTE.json` from static config inspection only |
| `scripts/audit/pal_clink_runner.py` | EXECUTOR | subprocess invoker for claude-audit/gemini-audit | AUTHORITY (OBSERVED) | `FORBIDDEN_CLI_NAMES={codex,codex-audit}`; **no production caller (dormant)** |
| `schemas/proof/embedded_audit.schema.json` | SCHEMA (version-locked) | n/a | AUTHORITY (VERIFIED_BY_PROOF) | `additionalProperties:false`; Codex absent from `auditor_tool` enum by deliberate exclusion; most schema-stable proof surface |
| Branch protection on `main` | GITHUB POLICY | n/a | AUTHORITY (GitHub API, authenticated) | strict=true; **8 required checks**; required human approvals=0; `enforce_admins=false` |
| Gemini automation lane (`gemini-dispatch.yml` + 5 more) | CI AUTOMATION | `contents: write` (gated) | AUTHORITY (OBSERVED) | Production-integrated; fork-protected; author-association gated; credential-gated |

### 2.4 Cockpit / dashboard surfaces (D4 §8.2 — only #1 is DCP-governed)

| Surface | Path | Classification | Tier | DCP Cockpit? |
|---|---|---|---|---|
| Governed TUI PM slice | `src/dopemux/ui/cockpit/` | AUTHORITY | VERIFIED_BY_PROOF | **YES** — the governed DCP operator cockpit (PM slice only) |
| neon_dashboard Textual app | `scripts/ui/neon_dashboard/` | ADAPTER | HISTORICAL (Feb–Mar 2026) | NO — separate monitoring app; no TP lineage; no explicit deprecation |
| "Palette" web (`ultra-ui-dashboard`) | `ui-dashboard/` (React/Vite/MUI) | UX_SURFACE | OPEN_PENDING (active Jun 2026) | NO (DCP-explicit per COCKPIT-0001) — ADHD Cognitive Dashboard; **but CURRENT-0001 frames it as "a second cockpit surface to inventory"** (CONTRA-03) |
| adhd-dashboard FastAPI | `services/adhd-dashboard/` | RUNTIME_SERVICE_PLANE | HISTORICAL | NO — ADHD API backing ui-dashboard |
| monitoring-dashboard FastAPI | `services/monitoring-dashboard/` (8098) | RUNTIME_SERVICE_PLANE | HISTORICAL | NO — system-ops health aggregator |
| Legacy `dashboard/` module | `dashboard/` (tmux selector) | ADAPTER | HISTORICAL | NO — predates governed cockpit |

### 2.5 Tooling surfaces (D4 Tooling; TOOLING-0001)

| Surface | Scale | Classification | Tier | Integration Mechanism |
|---|---|---|---|---|
| Lifecycle hooks | 10 (`.claude/settings.json`) | AUTHORITY | OBSERVED | Dispatched via `src/dopemux/claude/native_hooks.py` |
| Hook scripts | 8 (`.claude/hooks/`) | EXECUTOR | OBSERVED | Runtime behavior NOT verified (silent-failure risk) |
| Pre-commit guards | 12 local (`.pre-commit-config.yaml`) | AUTHORITY | OBSERVED | `.git/hooks/` empty → must run explicitly or via CI (bypassable) |
| Validation/proof/audit scripts | 60+ (`scripts/`) | REDLINE_GUARD | OBSERVED | Not all registered in pre-commit; fail-safe behavior UNKNOWN |
| Agent/persona definitions | 80 files | REFERENCE_ONLY | OBSERVED | Routing logic UNKNOWN |
| SKILL templates | 20 | REFERENCE_ONLY | OBSERVED | Discovery/instantiation mechanism UNKNOWN |
| Custom slash commands | 27 | WORK_GRAPH_SURFACE | OBSERVED | Harness auto-discovery NOT confirmed |
| Codex plugin | 1 (`plugins/dopemux-mission-control/.codex-plugin/`) | ADAPTER | OBSERVED | Loaded-in-Copilot status UNKNOWN |
| MCP config files | 2 (`task-master-mcp-config.json` + `mcp-system.md`) | ADAPTER | OBSERVED | References deprecated `mas-sequential-thinking` (drift) |

### 2.6 Cross-cutting authorities (D1, D3)

| Entity | Classification | Tier | Notes |
|---|---|---|---|
| ConPort (PostgreSQL AGE) | AUTHORITY | AGENTS.md §6 VERIFIED_BY_PROOF | Canonical knowledge-graph authority (durable) |
| `dopetask-canonical-spec.json` | AUTHORITY | OBSERVED (CI-enforced) | Schema target for all TP authoring; `Draft7Validator` |
| Dopetask adapter stack (`src/dopemux_pr_merge_specialist/dopetask_*`, 9 modules) | ADAPTER | OBSERVED | DCP-safe read path; ZERO subprocess (rg-confirmed); **except** PacketLauncher + SequentialPlanRunner = EXECUTOR (C-D1-CROSS) |
| `event_repo.py:91 EventRepository.append()` (dNh) | CANONICAL-WRITER SUBSTRATE | AUTHORITY (dNh runtime) | DCP must NEVER call directly; underlies dNh lanes 4/5/7 |
| `approval_policy.yaml` + `policy.py` (Dopemux) | AUTHORITY | OBSERVED | Machine-readable T0–TX tier system |

---

## 3. Task Orchestrator Deep Findings

**Anchor decision (BOUNDARY THE DECISION; spec §2):**
> DCP Core = evidence/readiness/proof/action-planning authority — it is **not** any of the four TO surfaces. It reads from them; it does not become them.
> - **jpicklyk TO (S1)** = projection / work-graph target (dry-run, read tools only).
> - **Dopemux FastAPI TO (S3)** = optional future cockpit / coordination bridge (NOT a DCP TO authority).
> - **Dopetask (S4)** = execution / proof-lifecycle adapter (campaign FORBIDS invocation).
> **Conflation of any two surfaces is FORBIDDEN.**

### 3.1 The naming collision (root cause of all prior confusion)

```
.mcp.json key  "task-orchestrator"      → S1: jpicklyk Docker MCP (stdio, SQLite)
compose.yml svc "task-orchestrator"     → S3: Dopemux FastAPI (HTTP :8000, in-memory)
```
Different products, state backends, transports, tool sets. Any analysis that conflates S1/S3 produces wrong authority classifications (BOUNDARY §8 row 1, RESOLVED by rescope).

### 3.2 S1 (jpicklyk) — WORK_GRAPH_SURFACE

- **Identity**: third-party MIT product, Kotlin/JVM, SHA256-pinned Docker image (label 3.8, created 2026-05-22, upgraded 2026-05-27). `.mcp.json` → bash wrapper `task-orchestrator-current-stdio.sh` (launch adapter, not custom tools). All 13 tools upstream.
- **13 tools**: 6 Write (`manage_items`, `create_work_tree`, `complete_tree`, `manage_notes`, `manage_dependencies`, `advance_item`) / 7 Read (`query_items`, `query_notes`, `query_dependencies`, `get_next_status`, `get_context`, `get_next_item`, `get_blocked_items`).
- **Lifecycle**: `queue → work → review → terminal` + `blocked`. Gate enforcement via note schema is **INACTIVE** — `.taskorchestrator/config.yaml` ABSENT (schema-free mode; all transitions unblocked by gate logic). DCP **cannot** rely on jpicklyk gates as a safety mechanism.
- **`advance_item`**: write-transition gate, cascades to ancestors, returns `allUnblockedItems[]` — **no dopemux-format proof receipt** (proof-envelope gap OPEN_PENDING).
- **State isolation**: `workspace_id = SHA256(project_root)[0:16]`; per-repo not per-worktree; per-client `--rm` containers. `USE_FLYWAY=true` hardcoded → migrations run on EVERY container start including read-only calls (read tools are not zero-cost).
- **Governance**: AGENTS.md §6 designates jpicklyk as workflow-transition authority. Decision #132 ("skip jpicklyk; use ConPort+Python ADHD Engine", in `_deprecated/`) is HISTORICAL/SUPERSEDED (C-D1-05).

### 3.3 S3 (FastAPI) — COORDINATION_SERVICE

- App title "Dopemux Plane Coordination API" v1.0.0, port 8000. PM↔Cognitive coordinator. **NOT** the jpicklyk product.
- **Mutating routes (live)**: `POST/PATCH /api/workflow/ideas`, `…/ideas/{id}/promote`, `POST/PATCH /api/workflow/epics`, `POST /api/coordination/{operations,events}`, `POST /api/coordination/conflicts/{id}/resolve` (in-process, NOT persisted), `POST /api/projects/{id}/workflow/transition`.
- **ABSENT at runtime**: `pm_tools` router NOT mounted (`/api/pm/work-items/*` unreachable; only `project_workflow_router` in `include_router`).
- **NO auth middleware on any route (VERIFIED)**: only `Depends(get_pm_config)` (config injection) + outbound bridge token found; `TASK_ORCHESTRATOR_API_KEY` env var NOT enforced. All mutation routes unauthenticated on dopemux-network.
- **Persistence**: `workflow_ideas`/`workflow_epics` → `WorkflowStore → DopeconBridge → ConPort custom_data`. All execution/PM state: `InMemoryExecutionStore`/`InMemoryLeaseStore`/`InMemoryPMTaskStore` — volatile.
- **Read-only MCP wrapper** (`mcp_wrappers.py`, added 2026-05-26): 6 tools all `read_only:True` (`status.queue`, `status.blockers`, `status.state`, `daily.summary`, `packet.validate`, `proof.validate`) → DCP-safe projection surface.
- `mcp_stdio.py` orphaned (not in `.mcp.json`). SSE: `/info` declares `/sse` 37 tools, but no `@app.get("/sse")` route found (UNKNOWN — may be FastMCP ASGI mount).
- **`server.py` S3→S1 coupling**: `subprocess.Popen` (line 141) spawns jpicklyk JAR; `server.py` NOT in Dockerfile COPY list → compose status OPEN_PENDING (C-D1-04).

### 3.4 S4 (Dopetask) — see §4. S5 — AUDITOR/DCP-adjacent

S5 (`src/dopemux/orchestrator/`): `transitions.py` (TransitionReceipt + idempotency), `policy.py` (T0–TX tier registry, YAML), `validation/proof.py` (proof-bundle shape validation), `github_adapter.py`, `perpacket.py`, `idempotency.py`, `memory_writers.py`. Imported by S3 MCP tool layer. **NOT ADHD automation.** `validation/proof.py` + `policy.py` are directly relevant to DCP proof contracts but are NOT enforced in live S3 routes (policy is dead enforcement at the route layer).

### 3.5 State, vocabulary, blockers

- **Split-brain state dirs** (C-D1-01/02, OPEN_PENDING): 7 dirs accepted (TP-0001's "5" is a stale earlier-pass artifact); active DB `dopemux-mvp-2e346e20…` (3.9MB, 262 work_items, mtime 2026-06-02) per two corroborating sources; TP-0001's `00c48dc6` is a prior session. Root cause (project_root path variation) OPEN_PENDING. DCP cannot project jpicklyk state until `TASK_ORCHESTRATOR_PROJECT_ROOT` is canonicalized.
- **Status-vocabulary fragmentation** (C-D1-10, OPEN_PENDING): `TaskStatus` (PENDING/IN_PROGRESS/COMPLETED/BLOCKED/NEEDS_BREAK/CONTEXT_SWITCH/PAUSED, ADHD-aware) vs `PacketState` (READY/LEASED/EXECUTING/PROOF_GENERATED/FAILED/CANCELLED/ABANDONED). No mapping layer; DCP render must handle both.
- **`LIVE_WRITE_READY` UNDEFINED** (master gate; `rg` → 0 results, TP-0004). All four surfaces DRY-RUN only by default.

---

## 4. Dopetask Deep Findings

### 4.1 Identity / authority

- v0.5.1 pinned via `.dopetask-pin`; installed on demand by `scripts/dopetask`; doctor passes all 6 checks. AGENTS.md §6 + quickstart §6 + ADR-220 = AUTHORITY (execution-plane).
- `scripts/taskx` = 7-line shim `exec ./dopetask "$@"` → eliminate from DCP design surface (C-D1, LOW).
- Authority rails: `.dopetaskroot` (empty marker, required) + `.dopetask-pin` + `.dopetask/project.json` (`project_id=dopemux-mvp`, `packet_required_header:true`).
- Canonical packet schema: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` (CI-validated).

### 4.2 Two distinct roles + safe read paths

Dopetask **writes** proof bundles during execution; DCP **reads** them via the mature adapter stack (`src/dopemux_pr_merge_specialist/dopetask_*`, 9 modules, ZERO subprocess — rg-confirmed).

**DCP-safe (read-only)**: `DopetaskAdapter` (without `launcher=`), `DopetaskBundleLoader`, `DopetaskSeriesLoader`, `DopetaskStatusMapper`, `DopetaskCompatibilityMode`, `DopetaskArchiveResolver`.

**MUTATION — DCP MUST NEVER INSTANTIATE**: `DopetaskPacketLauncher` (writes PROOF_BUNDLE.json, calls FlightDeckOpsEngine, internals UNKNOWN), `DopetaskSequentialPlanRunner`. **Critical guard**: `DopetaskAdapter.from_tp_id` with `launcher=` kwarg → MUTATION. Co-location in the adapter directory is NOT a safety signal (C-D1-CROSS).

### 4.3 Adapter contract invariants (DOPETASK-0002)

- `DopetaskAdapterResult`: 10 required sub-objects. `source` always `"dopetask"` (DCP discriminator); `schema_version` always `"1.0"`.
- `posture.mode` = pass-through identity, NEVER remapped — the GOVERNANCE authority field. `summary.headline_state` = DERIVED/display-only — DO NOT use for governance. `governance.signoff.required` mirrors `posture.signoff_required`.
- **Status truth table (5 rows)**: errors→ERROR; non-canonical+no-errors→DEGRADED; canonical+archive-expected-but-absent→DEGRADED; canonical+no-archive→READY; canonical+archive-present→READY.
- Bundle hard-required: `artifacts` + one of `{tp_id, pr_id}`. Expected-canonical (absence→DEGRADED): `{status, summary, acceptance_checks, validation, manifest}`. Archive expected iff `artifacts` non-empty; path = `bundle_path.parent.parent / f"{bundle_path.parent.name}.zip"`.
- **POSTURE → allowed actions**: `GO_FULL_AUTO`→APPLY_FIX+MERGE+APPROVE+MISSION_SUMMARY; `HOLD`/`UNKNOWN`→[]. `HIGH_RISK_AUTO_APPLY` blocked except GO_FULL_AUTO. **Governance fail-closed**: `aggregate_series_governance` intersection-based; non-VALIDATED series → MISSION_SUMMARY only.

### 4.4 Schema contradictions in adapter docs (code authoritative)

| Field | Doc says | Code says | Authority |
|---|---|---|---|
| `computed_at` | `float` Unix ts (`adapter-schema.md:147`) | `str`/ISO-8601 (`DopetaskStatusMapper:171`, `dopetask_adapter.py:330`) | **Code** (C-D1-06) |
| `integration.loaded_from` | 2 values (`adapter-schema.md:137`) | 4 values: `bundle/launch/canonical_bundle/compatibility_manifest` (`dopetask_adapter.py:189-193`) | **Code** (C-D1-07) |

### 4.5 Series contracts + critical gap

- Series JSON: required root `{series_id, project_id, status, packets}`; per-packet `{tp_id, status}` (+ optional `depends_on, is_final, bundle_path, title`); duplicate `tp_id` → `SeriesSchemaError`; DFS cycle + forward-ref check before any state returned.
- `SeriesStatus` (6): PLANNED/IN_PROGRESS/VALIDATED/FINALIZED/FAILED/UNKNOWN. `PacketStatus` (6): PLANNED/IN_PROGRESS/VALIDATED/FAILED/SKIPPED/UNKNOWN. Distinct enums (FINALIZED vs SKIPPED).
- **CRITICAL GAP (C-D1-08, OPEN_PENDING)**: No `.dopetask/series/` state.json exists (`find .dopetask -type f` → only `project.json`). `from_series_id` requires `.dopetask/series/<id>/state.json` (produced by `dopetask tp series status` CLI). **DCP has no series state to consume today; series claims are CLAIMED_ONLY.** Acquisition strategy UNDEFINED (3 unresolved options: pre-capture via CI / read-only CLI on demand / DCP generates from manifest).
- **No native `--dry-run`** (C-D1-16, OPEN_PENDING): v0.5.1 `tp series exec` help has only `--agent, --repo`. DCP dry-run posture must come from consuming pre-captured artifacts, NOT a dopetask dry-run flag.

### 4.6 Mutation inventory + corpus

- **Confirmed MUTATION (NEVER invoke)**: `tp series exec/finalize`, `tp run`, `tp exec`, `run-task`, `commit-run`, `commit-sequence`, `finish`, `loop`, `orchestrate`, `promote-run`, `init`, `compile-tasks`, `upgrade`, `pr`, `wt`, `tmux`, `collect-evidence`, `gate-allowlist`, `spec-feedback`, `ci-gate`.
- **UNKNOWN scope (avoid-by-default)**: `doctor`, `ops`, `docs`, `project`, `metrics`, `manifest`, `bundle`, `case`.
- **Confirmed read-only**: `tp series status`, `neon` (console-only).
- 682 task-packet files; `PACKET_ENGINE_MAP` maps only 3 TPs (TP-PRMS-052/053/054) → all others ValueError in launcher (EXECUTOR path only; DCP read path unaffected). DCP packet-generation path needs no execution: `prompts/gpt55-packet-forge.md` → validate against canonical spec.

---

## 5. Proof Contract Findings

### 5.1 Five incompatible proof-shape families coexist (PROOF-0001 §3)

| Family | Producer | Authority |
|---|---|---|
| AGENTS.md §9 Operational Bundle | Codex agent per TP | AUTHORITY — template (not schema-validated) |
| Skill-Bundle / PR Steward | Skill runtime | AUTHORITY — enforced by `orchestrator/validation/proof.py` |
| Orchestrator Governance Bundle | Orchestrator skill | AUTHORITY — `orchestrator/validation/proof.py` |
| System-Data ProofBundle (`schema_version=system-data-proof.v1`) | `system_data/proof.py` | AUTHORITY — runtime writer |
| Codex Handoff Template (`dopemux.codex_refresh.proof.v1`) | Codex handoff | ADAPTER — all null values (PSEUDOCODE) |

**Old assumption "single unified PROOF.json contract" is FALSE.** DCP must implement **shape-family dispatch**, not one validator.

### 5.2 Pointer-first; no unified generic pointer exists today

- Only observed generic cross-system pointer: **dNh RDCP `PROOF_POINTER.json`** (prior-campaign, `schema_version=1.0.0`): `adapter.{expected_head_sha, mutation_performed}`, `proof.{freshness_state, head_sha, packet_id, path, sha256, validation_status}`, `repo.{branch, head_sha, root}`.
- In dopemux-mvp: `DopetaskProofRef` is a Python dataclass only (not a file artifact); `DopetaskBundleLoader` uses heuristic 3-step filename search (not deterministic). PR Steward's `merge_readiness.schema.json` proof subobject is the closest analog but PR-Steward-scoped.
- **Synthesis decision (PROOF-0001 §9)**: Option A (adopt RDCP + extend), B (new DCP_PROOF_POINTER.json combining RDCP + PR-Steward freshness), C (shape-family dispatcher). Evidence supports B or C. **NOT decided in evidence campaign — UNKNOWN pending synthesis ruling.**

### 5.3 `auditorVerdict ≠ validationState` (DR-005/GATE-EXT-4) + three freshness mechanisms

- DR-005 mandates `PROOF.json` fields `headSha, dirtyWorktree, mixedShaArtifactSet, validationState, auditorVerdict` (auditorVerdict explicitly distinct from validationState). Never self-hash PROOF.json (hash from outer index).
- **Three distinct freshness mechanisms** (C-5, PRESERVED): SHA-match (PR Steward `proof_freshness` FRESH/STALE/MISSING; RDCP `freshness_state` CURRENT) vs lifecycle-phase (orchestrator `status` READY_FOR_REVIEW/VERIFIED — NOT freshness) vs checksum-integrity (dNh CRM `CHECKSUMS.sha256`). DCP requirement: pointer records `head_sha` at capture, derives `freshness_state` via sha-match; lifecycle status MUST NOT proxy for freshness.

### 5.4 Schema strictness: PASS_WITH_RISKS — risk in docs/templates, NOT in `schemas/` (SCHEMA-0001)

**SCHEMA-0001 WAS executed** (contra prior gap claim). The strict-schema/pseudocode concern is RESOLVED on the `schemas/` axis:
- All 12 `schemas/` files valid JSON with `$schema`; `additionalProperties:false` at every level. No pseudocode markers (rg → 0). Primary TaskPacket schema production-strict, runtime-validated by `Draft7Validator`.
- **Runtime schema validation exists ONLY for dopetask packets.** `tools/pr_steward/` + `tools/pr_action_bridge/` artifacts validated in tests only, NOT at runtime.
- **Pseudocode risk actually lives in**: `proof-contract.md` (narrative), `proof-bundle-template.json` (template), `codex-proof-template.json` (all null), `orchestrator/validation/proof.py` (schema implicit in Python, no JSON Schema file — HIGHER risk).
- **Safe-to-base fields** (enforcement-grade, `additionalProperties:false`): `embedded_audit.schema.json`, `merge_readiness.schema.json`, `bundle_manifest.schema.json`.
- **Known gaps**: `execution.agent` enum lacks `claude_code/grok/jules/github_copilot` (workaround: use `codex`; DCP MUST NOT infer agent identity from enum); 5 schemas lack `schema_version`; `pr_state_snapshot` has 4 intentionally-loose array items; `repair_packet.schema.json` uses draft 2020-12 (all others draft-07).

### 5.5 Embedded audit is the most schema-stable surface

`embedded_audit.schema.json` version-locked (stop-condition TP-DMX-AUDIT-PROOF-004; adding enum values requires a TP). Producer `tools/auditor_router/pal_clink.py:build_pal_clink_embedded_audit_object`. `status` enum PASS/PASS_WITH_RISKS/FAIL/NEEDS_SUPERVISOR/SKIPPED; `auditor_tool` enum excludes Codex by deliberate exclusion. **Status-name collision (C-2, PRESERVED)**: embedded-audit `status` (audit outcome) vs orchestrator `status` (lifecycle PLAN_ONLY..VERIFIED) — orthogonal axes, same field name. DCP MUST NOT conflate.

### 5.6 DCP generic pointer requirements (PROVISIONAL — 8 reqs from PROOF-0001 §D)

*(Requirement IDs PReq-1..8 here are distinct from the §14 decision IDs D1..D16.)* PReq-1 deterministic path + sha256; PReq-2 `shape_family`/`schema_version` discriminator; PReq-3 freshness via SHA-match not lifecycle; PReq-4 `mutation_performed` boolean guard; PReq-5 NEW artifact alongside existing PROOF.json (no retroactive migration of 30+ files); PReq-6 defer validation on template/governance-doc fields (PSEUDOCODE); PReq-7 support multi-bundle series (`proofs[]` array); PReq-8 optional `EVIDENCE_MANIFEST` companion. **Must NOT be in pointer**: full PROOF.json content, embedded_audit sub-object, run_id/skill/bundle_id, chain_of_custody, validation_state, any template-derived field.

---

## 6. PR / GitHub / CI Findings

### 6.1 PR Steward — advisory-only, schema-enforced (PR-0001, PASS_WITH_RISKS)

- `collector.py` (read-only `gh pr view`/`gh api graphql`), `classifier.py` (`mutation_performed=False` hardcoded ×6), `intake.py` (file artifacts only). All 5 `schemas/pr_steward/` define `mutation_performed: const false` — compile-time invariant. `merge_readiness.schema.json` `allOf` gate: READY requires `proof_freshness=FRESH` AND `matches_pr_head=true` AND non-empty `proof_head_sha`. GHA read-only perms; `continue-on-error:true`. Schema `1.1.0` const.
- **CRITICAL two-system distinction (C-3, RESOLVED on framing — keep both):** `tools/pr_steward/` (advisory) vs `src/dopemux_pr_merge_specialist/` (63 files, mutation-capable). `queue_drain.py:2017` = LIVE `gh pr merge --auto execute=True`; `queue_drain.py:1308` = `gh pr ready`. **`steward_gate.py` (designed fail-closed guard, TP-DMX-STEWARD-GATE-201) FILE DOES NOT EXIST.** A reader generalizing "PR Steward is advisory-only" to the whole PR-merge domain would wrongly conclude no mutation capability exists.
- **CLAIMED_ONLY (no proof bundles)**: TP-DMX-STEWARD-GATE-201, -PACKAGE-301, -SCAFFOLD-302, -DOCTOR-303, -AUTOREVIEW-HARDEN-401.
- `known_reviewers.json`: 5 project-specific entries — must be replaced for cross-project reuse.

### 6.2 Action Bridge — pure non-mutating function (ACTION-0001, PASS_WITH_RISKS)

- `compiler.py`: zero subprocess/gh/FS I/O; `mutation_performed:False` hardcoded; `action_plan.schema.json` `const false`. VERIFIED by TP-DMX-PR-ACTION-BRIDGE-006 (52 tests) + TP-DMX-COPILOT-REPAIR-007 (64 tests), both VERIFIED_BY_PROOF 2026-05-26. `repair_packet.schema.json`: `copilot_authority: const "implementer-only"`, `RepairItem.category` 4-enum (supervisor/CI categories structurally excluded).
- **Reuse (two-part)**: (1) PR-merge lane — DCP can call `compile_action_plan()` directly today; (2) non-PR-merge DCP actions (CRM/Telegram/identity/approvals) — NOT drop-in; taxonomy extension (`_BLOCKER_MAP`), not rebuild. **No production callers** (tests only); awaiting TP-102 CLI.
- **CLAIMED_ONLY (file-absent)**: TP-DMX-ACTIONBRIDGE-CLI-102 (`__main__.py`, `cli.py`, `scripts/pr-action-bridge`), TP-DMX-COPILOT-RENDERER-103 (`tools/copilot_repair/`).
- **CRITICAL mutation risk**: `scripts/batch_resolve_and_merge.py` (standalone, `resolveReviewThread` + `gh pr merge --squash`) NOT connected to compiler — must NEVER be called from DCP automation; no guardrail.

### 6.3 Auditor router / PAL clink — configuration AVAILABLE, execution DORMANT (AUDIT-0001, PASS_WITH_RISKS)

**AUDIT-0001 reconciliation (repo OUTRANKS DR-004):** DR-004 rated PAL clink UNKNOWN (external vendor docs). Repo runtime supersedes on the configuration axis: `claude-audit.json` + `gemini-audit.json` PRESENT, pass static safety inspection (`--permission-mode plan`, `--model sonnet`, `role_args=[]`), classifier returns AVAILABLE/LOW. **Two axes must not collapse**: Configuration = AVAILABLE; Execution/runtime = NEEDS_SUPERVISOR (binary presence unproven, `auth_status=NOT_CHECKED`, no production caller).

- `tools/auditor_router/` = pure STATIC classifier (no subprocess). `scripts/audit/pal_clink_runner.py` = actual EXECUTOR (`FORBIDDEN_CLI_NAMES={codex,codex-audit}`), no production caller (dormant). `preflight.py` static-only by design; `noninteractive_mode_proven=True` means proven by static config inspection ONLY (naming potentially misleading).
- **Codex**: FORBIDDEN at code level (`FORBIDDEN_CLI_NAMES`) AND schema level (absent from enum) — defense-in-depth, not UNKNOWN. **Copilot**: `_contains_copilot_audit()` → TOOLING_UNSAFE/HIGH. **AGY/Antigravity**: schema-valid + prompt, but zero clink config/preflight/proof — UNKNOWN on all execution axes.
- **Known bug**: 3 hardening tests use bare `from auditor_router…` instead of `from tools.auditor_router…` → `ModuleNotFoundError` on standard pytest.
- **Proof-bundle contradiction (C-4, PRESERVED)**: `PROOF.json route_behavior.pal_clink_attempt_result=SANDBOX_BLOCKED` vs `PAL_CLINK_AUDIT_OUTPUT.json return_code=0` (genuine successful run, 12 files read). Machine consumer would conclude clink failed; it passed. PROOF.json route_behavior is stale.

### 6.4 Branch protection — ACTIVE, 8 required checks, strict (GITHUB-0001, PASS)

- `gh api .../branches/main/protection`: `strict=true`; `required_approving_review_count: 0`; `required_conversation_resolution: true`; `required_linear_history: true`; no force-push/deletion; **`enforce_admins.enabled: false`** (admins can bypass — UNKNOWN if org policy closes gap).
- **8 required checks**: Security Review, Documentation, identity-check, Unit Tests, CodeQL ×3 (ruby/python/js-ts), CI Pipeline Summary.
- `.repo_id` validated every push/PR/merge_group (`project=dopemux-mvp, owner=hu3mann`).
- **Gemini lane production-integrated (overturns "experimental")**: `gemini-dispatch.yml` (236 lines) auto-routes; fork-protection (`head.repo.fork==false`); author-association gate (OWNER/MEMBER/COLLABORATOR); credential gating (`detect_gemini_credentials`); `gemini-plan-execute.yml` has `contents:write, pull-requests:write, id-token:write` (real write, gated by all 8 checks). `rg pull_request_target .github` → 0 (no injection foot-gun).
- **CODEOWNERS**: single `@hu3mann` owns all paths — no backup approval path. Secondary ruleset "Default branch protection (restored after history rewrite)" (ID 13063360, active) — granular conditions UNKNOWN (admin scope), NEEDS_SUPERVISOR.

---

## 7. Runtime Boundary / Red-Lane Findings

### 7.1 Three-bucket split (RUNTIME-0001; D3 §7)

Red lanes split into three non-overlapping governance buckets. **Membership lists are authoritative over numeric totals** (the task framing's "7 generic / 8 Dopemux / 12 dNh" does not exactly match the enumeration; ~8 generic / 7 Dopemux / 11 confirmed + 1 probable dNh — the mismatch is acknowledged and does not affect per-lane evidence).

**Generic red lanes (all projects):** branch-protection mutation; CODEOWNERS changes; `.github/workflows/` permission escalation; secret exposure in argv/cache/logs; self-certifying implementer/auditor/supervisor loop; `pull_request_target` + untrusted-checkout; proof contract/schema mutation; agent-approved merge without supervisor.

**Dopemux-specific:** `DPMX_LIVE_OK` dual-consent gate (live API needs `--execute` AND `DPMX_LIVE_OK=1`; removing gate is itself T6); `scripts/dopetask` exec without consent; chronicle/dope-memory append via `services/mcp-capture/server.py:62` (mcp-capture = canonical write gateway; DCP must NEVER call chronicle append directly); GitHub PR merge via pr_merge_specialist (T5); approval-policy fingerprint mutation (`validation.py:102`); TO live-write (LIVE_WRITE_READY UNDEFINED, OPEN_PENDING); launchd service management (T6).

**dNh-specific (11 confirmed + 1 probable, from `ARCHITECTURE_SYNTHESIS.md §4.3`):** (1) Telegram send; (2) Telegram approval callbacks; (3) iMessage/AppleScript + chat.db FDA ingest; (4) Twenty CRM writeback; (5) identity/contact merge (irreversible); (6) approval-policy rule mutation; (7) mirror-dispatcher dedupe-claim write; (8) RAG draft/worker index write (`rag_worker.lock` dirty — likely running, status UNKNOWN); (9) OpenClaw/browser automation (naming constant, active status UNKNOWN); (10) proof contract/bundle authorship; (11) CI/branch-protection change (state UNKNOWN); **(12) probable WhatsApp outbound (UNKNOWN — not in §4.3 enumeration)**.

**Canonical-writer substrate (not a numbered lane):** `event_repo.py:91 EventRepository.append()` — DCP must NEVER call directly; underlies lanes 4/5/7.

**Confirmed negatives (boundary findings, not red lanes):** PR Action Bridge compiler read-only; Dopemux PR Steward workflow read-only; `pr_steward/classifier.py` is CI-check/author-trust only — **Dopemux has no runtime file-path red-lane classifier** (grep `red_lane` = 0).

### 7.2 Approval tier system (Dopemux — machine-readable)

`config/orchestrator/approval_policy.yaml` enforced by `orchestrator/policy.py`:
| Tier | Meaning | DCP Implication |
|---|---|---|
| T0–T1 | Auto-invocable | DCP may invoke without supervisor |
| T2–T4 | Gated (escalating) | Operator confirmation; T4 = chronicle append, fingerprint mutation |
| T5 | GitHub mutation gated | No GitHub merge without supervisor; pr_merge_specialist = bounded executor |
| T6 | Destructive + typed confirmation | launchd, LIVE_WRITE_READY-scope, removing DPMX_LIVE_OK |
| TX | Unknown capability | Default: refuse |

**Lane-overlap tension (PRESERVED, not a dedup error):** several lanes are generic in policy but project-specific in runtime manifestation (branch-protection, proof-schema mutation, browser/OpenClaw, CODEOWNERS, live-write/provider-API). `gemini-dispatch.yml` holds `pull-requests:write` at GHA level; T5-gate applies at the orchestrator layer, NOT the GHA permission layer (C3 RED_LANE §8). GHA grants capability; orchestrator enforces policy; **neither overrides the other**.

---

## 8. UX / Cockpit Findings

### 8.1 Cockpit-under-construction — layered, NOT greenfield, NOT "built" (COCKPIT-0001)

**Do not collapse to "built" or "greenfield."**

- **Layer A — Governed TUI PM slice (AUTHORITY, VERIFIED_BY_PROOF)**: `src/dopemux/ui/cockpit/` — `app.py` (Textual, 126 LOC), `render.py` (deterministic PM renderer, 353 LOC, "single source of truth"), `runtime_contract.py` (1854 LOC, IA contract w/ UNKNOWN/Drift/Settings/SafeActions). CLI `cockpit_commands.py` guarded by `--runtime-render`, static demo, NO live writes. Unit-tested.
- **Layer B — pack merge status (INTRA-PACKET CONTRADICTION, CONTRA-01/06, PRESERVED)**: §3 VERIFIED_BY_PROOF (2026-06-03) says pack PRs #568–573 MERGED to origin/main; §7/§9 prose (STALE, traced to a 2026-05-02 README) say "NOT merged / BLOCKED preflight." **VERIFIED_BY_PROOF outranks HISTORICAL → pack IS on main**, but COCKPIT-0001 is internally inconsistent; synthesis must not treat it as uniform-authority.
- **Layer C — new cockpit wave (OBSERVED, OPEN_PENDING)**: PRs #731–749 (command-palette broker, safe-action typed gates, frame rules, design-gate flip) merged to `claude/hungry-buck-67a0d3` **only — NOT on origin/main**.
- **Layer D — implementer mode (NOT built)**: only PM slice implemented; `render_implementer` absent.
- **Layer E — TP design-gating (CLAIMED_ONLY)**: 13 `out/cockpit-*` dirs; **all carry `safe_for_claude_design: "NO"` / `ready_for_claude_design: false`** — no cockpit surface cleared for Claude Design final screens.
- **DR-010 MVP ordering (REFERENCE_ONLY)**: artifacts → CLI → TUI (optional read-only) → projection adapters → web later. "Risk instrument panel, not green-badge theatre." Current PM-slice CockpitApp matches the TUI prescription; risk panel not yet built.

**Key distinction**: code merged ≠ design cleared. The PM slice is on main AND design-gating remains active — not contradictory.

### 8.2 Operator journey / step count (UX-0001 — current state, targets DEFERRED)

| Cycle | Current | Automation status |
|---|---|---|
| Evidence Harvest | ~186 bash lines/packet; 18 packets serial ≈ 3.6 hrs | 5–8× speedup if 5-way parallel (DEFERRED UX-0003) |
| Research | 13 DR pre-cached; 1 consumer sync | async prefetch candidate; staleness model UNKNOWN |
| Synthesis | 7 done + 6 in-flight; ~270 lines/packet | copy-paste heavy; "synthesis accelerator" candidate |
| Packet Execution | ~15 min/packet serial | job-queue/async possible; interdependencies block naive parallelization |
| Audit | 0 embedded audit (by design) | proof-diff→Opus candidate (DEFERRED) |
| Acceptance | 1 supervisor binary gate | NEVER-automate (human judgment) |
| Next-Packet Gen | 0 automated | auto-generate TP series from synthesis + approval (DESIGN) |

**Target step counts + L0–L7 automation ladder DEFERRED to Stage 2** (UX-0002 placement, UX-0003 ladder are design packets, not evidence).

### 8.3 Tooling-Layer subsection (TOOLING-0001)

**Deterministic infra exists at scale** (see §2.5): 10 hooks, 12 pre-commit guards, 80 personas, 20 skills, 27 commands, 60+ validators. The synthesis question is not "does tooling exist" but "which surfaces should DCP standardize as deterministic hooks vs leave to LLM instruction."

**Three decisions requested (TOOLING-0001 §9):** (1) which surfaces → deterministic hooks vs LLM instruction; (2) centralized skill/agent/command registry vs distributed discovery; (3) enforce MCP config schema + deprecation tracking?

**Tooling contradictions (CONTRA-05, PRESERVED):** `task-master-mcp-config.json` references deprecated `mas-sequential-thinking` (claude.md declares it replaced by PAL) → incomplete migration, silent-auth-failure risk. Agent runtime authority DISTRIBUTED-vs-governed (AGENTS.md §6/§10 mark it UNKNOWN; 80 personas + 27 commands imply distributed system). Skill-template instantiation UNKNOWN. Hook dispatcher split (`.claude/hooks/` scripts vs `src/dopemux/claude/native_hooks.py` dispatcher).

**Tooling UNKNOWNs (do not upgrade):** hook runtime faithfulness; skill→active-skill mechanism; persona routing logic; MCP config currency (loaded vs declared); pre-commit bypass risk (`.git/hooks/` empty); `generate_provision_proof.py` ↔ AGENTS.md §9 alignment; AGENTS.md/claude.md/governance-principles.md sync.

---

## 9. External Research Findings

**Authority class (ALL DR): `VENDOR_DOCS / EXTERNAL_CONSTRAINT_SYNTHESIS / LOWER_THAN_REPO_RUNTIME`. Repo runtime outranks every item. Corroboration ≠ authority promotion** (C3 systemic tension — any synthesis reading corroboration as validation has introduced authority laundering). DR reports do NOT carry §8/§11 template sections; external contradictions are flagged `EXTERNAL_vs_REPO`.

### 9.1 Per-report load-bearing facts (DR-001..016)

- **DR-001 (GitHub/Merge)**: GitHub is merge authority; one stable required gate (`pull_request`+`merge_group`) + advisory PR Steward; `ready_for_review` not in default trigger; required-check truth table (workflow-skipped→Pending blocks, job-skipped→Success); accepted conclusions `success|skipped|neutral`; harvest BOTH classic + ruleset protection; `pull_request_target`+untrusted = hard block. Feeds GITHUB/PR/OPENPRS-0001.
- **DR-002 (Copilot)**: bounded implementer only — never approve/merge/mark-ready/resolve-threads; current docs say `@copilot` pushes to PR branch by default; Copilot-pushed workflows held until human approves; agent secrets separate. **UNKNOWN**: whether repo's Copilot integration respects held-workflow rule. Feeds ACTION-0001.
- **DR-003 (MCP/TO write contract)**: MCP = plumbing, not write-safety; annotations are untrusted hints (host enforces class); **three separate tools** (read/dry-run/live), not a flag; dry-run returns proof bundle (immutable target IDs, canonical payload, fingerprint, preconditions, idempotency-key preview, preview hash); live-write requires dry-run-hash + write_intent_id + durable idempotency_key + preconditions + read-after-write + append-only receipt + rollback mode; own `dopemux.io/*` namespace. **Corroborates** TO projection-first + undefined LIVE_WRITE_READY.
- **DR-004 (Auditor capabilities)**: default ordering Codex-first (hard-RO sandbox) → Gemini-second (sandbox off; plan mode "not fully functional"; **Antigravity replaces Gemini CLI 2026-06-18 for some tiers**) → Claude soft/policy-RO-only (NEEDS_SUPERVISOR for hard-RO) → Copilot locally-proven-only → AGY+PAL clink UNKNOWN (external). Min proof envelope: raw stdout/stderr, exit code, invocation, binary version, model id, output SHA-256. **EXTERNAL_vs_REPO**: rates PAL clink UNKNOWN, but repo HAS `pal_clink.py` — the discriminating tension; reconcile in AUDIT-0001 (do not upgrade from UNKNOWN on DR-004 alone).
- **DR-005 (Proof/Provenance)**: COMPOSE existing standards (in-toto Statement, DSSE, SLSA provenance, SLSA VSA, Sigstore, SPDX/CycloneDX) — do not invent DCP-native format; pointer-first by digest; `CONTROL_PROOF_POINTERS.json` = discovery, `PROOF.json` = machine summary (mandatory `headSha, dirtyWorktree, mixedShaArtifactSet, validationState, auditorVerdict`); never self-hash PROOF.json; grades traceable→replayable→deterministically-replayable→release-grade. Feeds PROOF-0001.
- **DR-006 (SQLite/Event-store)**: append-only system of record (single writer, WAL, local FS); **snapshot-first exporter** (RO open → Backup API → reopen `immutable=1`; never checkpoint/journal-flip/raw-copy/`nolock`; `query_only` is NOT a safety rail); two idempotency identities (semantic caller key + RFC-8785 canonical hash); transactional outbox = at-least-once + dedupe (exactly-once is a lie); disable external gateways during replay; version floor 3.51.3/3.50.7/3.44.6. Feeds STATE/event-store lane.
- **DR-007 (macOS/iMessage/TCC/launchd)**: chat.db needs FDA for exact responsible binary (not Files&Folders, not SIP); launchd does NOT inherit Terminal FDA; safe read = snapshot-first; hard red lines (supervisor+consent): auto-grant FDA, reset TCC, disable SIP, upload chat.db. Feeds RUNTIME/XPROJ.
- **DR-008 (Telegram)**: `callback_data` 1–64 bytes (opaque single-use action_id only; context server-side); at-least-once → dedupe on `update_id`+`callback_query.id`, effect on `action_id`+`effect_id`; pre-bind before send (user/chat/message/thread/policy-hash/proof-pointer/expiry); `answerCallbackQuery` ~10s; **Telegram = evidence/channel, never sole authority**. Feeds RUNTIME.
- **DR-009 (Twenty CRM)**: schema tenant-generated (introspection API; public docs lag); no native idempotency header → DCP owns dedupe (unique `externalId`/`proofId` + upsert, match one unique key: People=email, Companies=domain); zero/multi-match → stop+escalate; coarse OAuth → least-privilege via roles, one client per lane; no audit-log API → DCP owns immutable ledger; hard red lines: Metadata writes, deletes, identity/relation changes, ambiguous match, Send Email. Feeds RUNTIME/XPROJ.
- **DR-010 (Cockpit UX)**: artifact-first truth + CLI primary + read-only TUI + GitHub/TO projection + web deferred; **risk instrument panel not green-badge theatre**; unknowns/incomplete are first-class display states; every surface badges Authoritative/Derived/Projection; automate detection/summarization/proof-collection/watch/route-suggestion; keep manual live-writes/red-lane-approval/route-override/merge; MVP = canonical MD/JSON + `dopemux` CLI + GitHub check-summary projection + optional TUI. **Corroborates** cockpit-under-construction.
- **DR-011 (Control-plane patterns — the architecture steer)**: **DCP ≈ Backstage (catalog/portal) + OPA (policy decision ≠ enforcement) + provenance-verifier + thin supervised action-broker**; DCP is **NOT** Temporal/Argo/Tekton/Humanitec (no durable execution, no runtime authority, no replay); DCP OWNS normalization/derived-status/proof-verification/policy-interpretation/action-intent; does NOT own durable queues/replay/retries/deploy-graphs/mutable-runtime-truth; tasks/workflows = projections (source_system, source_ref, observed_at, freshness, deep-links); capability-based adapter contract (`entity.read`/`observation.stream`/`evidence.stream`/`action.dry_run`/`action.submit` → returns external authority ref). **Corroborates** TO projection-first. **DR-011 tension (D3 §9.6, PRESERVED)**: XPROJ §4 classifies REFERENCE_ONLY/advisory; XPROJ §11 says "upgrade to VERIFIED_BY_PROOF / authoritative design template." Resolution: file existence = OBSERVED, but authority TIER stays advisory — must not outrank runtime code; validate each field against observed runtime before committing to schema.
- **DR-012 (Agent automation security)**: **two-phase gate** (unprivileged: no secrets, minimal token, reads untrusted only → privileged: acts only on bounded evidence — hashes/verdicts/attestations, never raw untrusted or arbitrary model output; taint everything outside trusted policy/config path); secret hierarchy OIDC→broker→GH-secrets→PAT(break-glass); never `pull_request_target`+untrusted, pin actions to full SHA, no secrets in argv/cache; **role separation hard rule** (implementer≠auditor≠supervisor; no self-certifying loop; no agent marks own work ready); MCP sub-rules (per-server scoped creds, pinned schema hashes, `additionalProperties:false`, no shell passthrough, server isolation); PR comments/external docs = data not authority; model output = tainted input. Feeds AUDIT/ACTION.
- **DR-013 (External synthesis — PARTIAL/FAIL-CLOSED)**: ran WITHOUT repo mounted (intentional). Produced 8 constraints but explicitly: `ACCEPT_AS_EXTERNAL_BASELINE`, `DO_NOT_TREAT_AS_RUNTIME_VALIDATION`, `DO_NOT_USE_AS_FINAL_ARCHITECTURE`, `FEED_INTO_5.5_SYNTHESIS_PACK`. **`DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md` was NOT found / NOT produced.** Synthesis must treat any such ledger as NOT YET PRODUCED.
- **DR-014 (Memory/Context/Chronicle patterns — single most load-bearing external constraint)**: **hard layer separation `source-truth ≠ index ≠ projection ≠ chronicle ≠ proof`** (each an architectural citizen, never cosplaying another); `authority_tier ⊥ confidence` (orthogonal; a mirror can be high-confidence + non-authoritative); **four freshness clocks** (source/index/retrieval/artifact, never merged into one `updated_at`); mirrors/bridges default non-authoritative read-only; roles — decision-store=intent/rationale/owner/supersession (NOT receipts/proofs/embeddings/logs), retrieval=rebuildable/source-pointed/never-legal-truth, chronicle=append-only temporal receipts/corrections-via-compensating-events/NOT-runtime-state, proof=external-verifiable/referenced-by-receipts/never-inlined, cockpit-timeline=projection-only/must-badge; **V1 = READ-ONLY across all adapters except optional DCP-owned append-only chronicle namespace**. Anti-patterns to preserve: retrieval-as-truth, mirror-as-authority, bridge-as-authority, chronicle-as-runtime-state, progress-as-workflow-legality, cache-freshness-as-source-freshness, cockpit-as-proof, confidence-as-authority, propagated-context-as-memory, summary-without-lineage. **Repo (MEMCTX-0001) outranks where conflicting.**
- **DR-015 (Tooling layer)**: core directive **`BUILD_AFTER_CORE_CONTRACTS`** (lock first: red-lane taxonomy / receipt schema / mutation classes / approval artifact / project path+resource maps); control split "LLMs reason → hooks enforce → CLI standardizes → proof records → supervisor decides"; deterministic (hooks/CLI: forbidden-path, schema, receipts, red-lines, hard blocks in UserPromptExpansion+PreToolUse+pre-commit+CI) vs LLM (skills/subagents: teach/synthesize/author, advisory); "probabilistic guard = vibe plane, not a red-lane gate"; plugin V1 `defaultEnabled:false`, no monitors/channels/default-agent-override, side-effectful skills `disable-model-invocation:true`; cross-project packaging `dcp-core` + `dcp-profile-dopemux` + `dcp-profile-dnh-crm` + repo-local (extend via rules/schemas/path-maps, not forked prompts; repo-local must not weaken core denies); NEVER build channels/default-agent-override/auto-approve-merge-resolve/CRM-client-send-from-skills/broad-live-writer-plugin; client-side Git hooks bypassable (`--no-verify`) → duplicate in CI.
- **DR-016 (Memory+Tooling consolidation — most COMPRESS-ready)**: ledger directs "COMPRESS should read this file directly." 10 severity-rated constraints (→ §9.2 gates). Six ready-made contract specs (see §12 options + below): Evidence-Hit (17 fields), Chronicle-Receipt (~24 fields), Memory/Context Adapter (role/ownership/write-perms/authority/freshness/mutation-type), Helper-Receipt (~20 fields), Red-line Hook (block>ask>warn>allow precedence; intercept prompt-expansion+tool-use; receipts even on denial), Plugin/Skill Manifest (mutation-class/allowed-tools/model-invocation-limits/opt-in; v1 defaultEnabled:false). DR-016 §7 lists 13 repo-only UNKNOWNs (see §13).

### 9.2 The 10 external-constraint gates (verbatim, for embedding in the GPT-5.5 prompt)

```
EXTERNAL CONSTRAINT GATES (DR-DCP-001..016)
Authority: VENDOR_DOCS / LOWER_THAN_REPO_RUNTIME
Corroboration of repo findings does NOT promote these to runtime rank.

GATE-EXT-1 [GitHub Merge Authority]
  GitHub is merge authority; DCP uses exactly one stable required gate + advisory PR Steward.
  Harvest BOTH classic and ruleset-based branch protection, bound to latest/queue SHA.
  Accepted check conclusions: success | skipped | neutral only.
  Blocked: pull_request_target + untrusted checkout (repo-compromise foot-gun).
  Source: DR-001. Feeds: GITHUB-0001, PR-0001.

GATE-EXT-2 [Task Orchestrator Projection-Only]
  Task Orchestrator (TO) is a projection surface, not an execution authority.
  Live writes only behind a proven three-lane contract: read-only / dry-run / live-write.
  Live-write requires: dry-run proof hash + write_intent_id + durable idempotency_key
    + preconditions + read-after-write verify + append-only receipt + declared rollback mode.
  Per ledger DR-003 corroboration note: repo campaign observed `LIVE_WRITE_READY` undefined,
    consistent with this gate — but repo runtime (TO-0002/TO-0004 packets) is authoritative;
    D5 carries this as corroboration, not D5-verified repo fact.
  Source: DR-003, DR-011. Feeds: TO-0002, TO-0004.

GATE-EXT-3 [MCP Tool Class Enforcement]
  MCP tool annotations (readOnlyHint etc.) are hints, not safety contracts. Host enforces class.
  Three separate tools required (read/dry-run/live), not a flag on one tool.
  Own namespace: dopemux.io/* for _meta fields.
  Source: DR-003. Feeds: TO-0002, ACTION-0001.

GATE-EXT-4 [Proof Pointer-First / auditorVerdict ≠ validationState]
  Proof is pointer-first, digest-anchored, chain-of-custody preserving.
  Compose existing standards (in-toto / DSSE / SLSA / Sigstore / SPDX/CycloneDX).
  auditorVerdict is a separate mandatory field from validationState; never conflate.
  Never self-hash PROOF.json; hash from outer index.
  No self-certifying proof (implementer ≠ auditor ≠ supervisor).
  Source: DR-005, DR-012, DR-016. Feeds: PROOF-0001, AUDIT-0001.

GATE-EXT-5 [Event-Store Snapshot Discipline]
  SQLite event-store reads use Backup API → immutable snapshot; never mutate live DB.
  query_only pragma is NOT a safety rail.
  Idempotency: semantic caller key + canonical request hash (RFC 8785).
  Outbox = at-least-once + idempotent sinks; disable external gateways during replay.
  Version floor: SQLite 3.51.3 / 3.50.7 / 3.44.6 (WAL-reset fix).
  Source: DR-006. Feeds: STATE-0001.

GATE-EXT-6 [Red-Lane Write Discipline]
  Red-lane writes (CRM, Telegram, iMessage/macOS, identity, approval-policy) require:
    supervisor gate, exact-match resolution (zero-match or multi-match → stop+escalate),
    reserved correlation IDs, and an independent proof ledger.
  Telegram = evidence/channel only, never sole approval authority.
  Twenty CRM: DCP owns dedupe via externalId+upsert; no native idempotency header.
  macOS/iMessage: FDA on the real binary; launchd does not inherit Terminal FDA.
  Source: DR-007, DR-008, DR-009. Feeds: RUNTIME-0001, XPROJ-0001.

GATE-EXT-7 [Two-Phase Agent Security / Role Separation]
  Unprivileged phase: no secrets, minimal token, reads untrusted artifacts only.
  Privileged phase: acts only on bounded evidence (hashes/verdicts/attestations),
    never on raw model output or untrusted PR content.
  Role separation: implementer ≠ auditor ≠ supervisor. No self-certifying loop.
  No agent marks its own work ready, approves its own PR, or resolves its own review.
  MCP: per-server scoped creds, pinned schema hashes, additionalProperties:false.
  Source: DR-012, DR-002. Feeds: AUDIT-0001, ACTION-0001.

GATE-EXT-8 [Layer Separation + authority_tier ⊥ confidence + Cockpit = Projection]
  Hard separation: source-truth ≠ index ≠ projection ≠ chronicle ≠ proof.
  authority_tier and confidence are orthogonal; never derive one from the other.
  Four freshness clocks must be carried separately (source / index / retrieval / artifact).
  Chronicle = append-only; corrections via compensating events, never in-place edits.
  Proof = pointer-first, referenced from receipts, never inlined.
  V1 = read-only across all adapters except DCP-owned append-only chronicle.
  Cockpit and Task Orchestrator are projection/visibility surfaces, not authority surfaces;
    every surface must badge authority class, freshness, completeness, and direct-vs-derived;
    cockpit visibility or proof presence does NOT constitute approval or legality.
  Source: DR-010, DR-014, DR-016. Feeds: MEMCTX-0001, CHRONICLE-0001, RETRIEVAL-0001,
    COCKPIT-0001.

GATE-EXT-9 [Build Tooling After Core Contracts / No Hidden Authority]
  Lock before tooling: red-lane taxonomy / receipt schema / mutation classes /
    approval artifact / project path+resource maps.
  Deterministic hooks + CLI outrank LLM advice for enforcement decisions.
  Plugin v1: defaultEnabled:false, no monitors, no channels, no default-agent override.
  Side-effectful skills: disable-model-invocation:true.
  Client-side Git hooks are bypassable; duplicate critical gates in CI.
  NEVER: auto-approve, auto-merge, CRM/client send from skills, broad live-writer plugin.
  Source: DR-015, DR-016. Feeds: TOOLING-0001, HOOKS, PLUGIN packets.

GATE-EXT-10 [Unknown Runtime State Fails Closed / No Repo Self-Certification]
  Any architecture claim that depends on actual repo behavior is provisional until
    repo runtime evidence confirms it.
  DR-013 ran PARTIAL/FAIL-CLOSED (no repo mounted) — its outputs are external baseline only.
  PAL clink rated UNKNOWN externally (DR-004); ledger notes repo has pal_clink.py
    (per DR-004 ledger corroboration note — not D5-verified); external blindness ≠ repo
    capability; reconcile in AUDIT-0001 via repo runtime evidence before promoting to KNOWN.
  DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md was NOT produced by the DR campaign.
  Source: DR-013, DR-004. Feeds: AUDIT-0001, all synthesis packets.
```

---

## 10. Open PR Authority Findings (CLAIMED_ONLY)

**All open PRs and generated TP series are CLAIMED_ONLY per spec §5 (in-flight classification model).** Open PR code = direction, not authority; open PR comments = review-signal, not truth.

### 10.1 Merged vs open (OPENPRS-0001, PASS_WITH_RISKS)

- **Merged — AUTHORITY (state=MERGED, checks=SUCCESS)**: PR #758 (Action Bridge CLI), #760 (Copilot repair packet), #761 (embedded audit CI), #762 (E2E autoreview fixture).
- **PR #758 contradiction (C-1, PRESERVED — DO NOT pick a winner)**: OPENPRS-0001 §4 reports #758 MERGED; ACTION-0001 §3 reports the TP-102 CLI files (`__main__.py`, `cli.py`, `scripts/pr-action-bridge`) ALL FILE-ABSENT in the working tree (feat/adhd-cognitive-remediation HEAD 71c6b51c). Possible: files in main but not feature-branch HEAD. **Synthesis must verify against `main`, not the feature-branch working tree the evidence reads used.**

| PR range | Content | Stack dependency | Proof |
|---|---|---|---|
| #765–767 | steward_gate stack (guard / seams / finalization) | #767→#766→#765→main (CASCADE REQUIRED) | ABSENT |
| #770 | pr-steward CLI (`dopemux pr-steward`) | Draft, independent | ABSENT |
| #775 | pr-steward doctor subcommand | Draft, independent | ABSENT |
| #776–790 | ADHD feature cluster | 15-PR linear stack | ABSENT |
| #791 | Palette UI refinement | Non-draft, independent | ABSENT |

**Total: 25 open PRs, 0 proof bundles.** No TP numbers assigned to #765–791; proof-bundle SLA UNKNOWN.

### 10.2 Binding merge-order + integration blocker

- steward_gate cascade #765→#766→#767 (out-of-order fails). ADHD cluster #776–790 = 15-PR linear chain; partial merges risk incomplete operator state; no integrated E2E test.
- **DCP integration blocker**: `queue_drain.py:2017` merge seam UNGUARDED; `steward_gate.py` ABSENT; PR #765 (steward_gate library) OPEN/CLAIMED_ONLY. DCP MUST NOT wire the PR-merge domain until (1) #765 merged + proof validated; (2) whether `execute=True` is production-reachable is traced (UNKNOWN).
- **Stale-spec contradiction (PRESERVED)**: v1 spec listed #758–767; current evidence: #758–762 MERGED (v1 stale), open stack = #765–791 (25 PRs, not 7).
- Gemini agent assignment: 87/91 packets `execution.agent="codex"`; 2 "gemini"; 2 blank (UNKNOWN).

### 10.3 In-flight series (CLAIMED_ONLY, from INTENT-0001 / CURRENT-0001)

| Series | Packets | Proofs | State |
|---|---|---|---|
| DMX-AUTOREVIEW-PLATFORM | 12 (101–106, 201–203, 301–303) + Harden-401 | 3 of 12+ | BLOCKED — Harden-401 no proof; 11 deps unverified |
| DMX-ORCH-INTEGRATION | 24 (001–017 + FOLLOWUP) | 0 | STAGED, NOT EXECUTING |
| RTE sub-series | 14 across 5 sub-series | 6 (partial) | FRAGMENTED — no unified root |
| COCKPIT series | 8 (MAIN-STATE-RECON-001 orphaned) | 0 | CLAIMED_ONLY; structure ambiguous |

The autoreview/PR-steward stack (DMX-AUTOREVIEW-PLATFORM 13 TPs + `src/dopemux_pr_merge_specialist/` 60+ modules with compiled .pyc) is the **largest surface in the repo and entirely CLAIMED_ONLY**. Synthesis must decide adopt / quarantine / mine.

---

## 11. Contradictions To Preserve

Aggregated from every packet's §8 + drafters' noted contradictions. **DO NOT resolve.** Status labels are carried verbatim from source drafters (RESOLVED-per-source rows are kept as record; genuinely-open cross-packet rows are kept open). De-duplicated where the same contradiction recurred across drafters (LIVE_WRITE_READY-undefined, PAL-clink-external-vs-repo, state-dir 5-vs-7 are single rows).

| # | Contradiction | Sources | Status |
|---|---|---|---|
| K-01 | "task-orchestrator" = one system vs two separate products sharing the name (S1 jpicklyk MCP vs S3 FastAPI) | BOUNDARY §8; TP-0001/0002/0003 | RESOLVED by rescope (separate + conflation forbidden) |
| K-02 | State-dir count: TP-0001 "5" vs TP-0002/0004 "7" | BOUNDARY §8; C-D1-01 | RESOLVED per BOUNDARY: 7 accepted; "5" is stale earlier-pass artifact; root cause OPEN_PENDING |
| K-03 | Active hash: TP-0001 `00c48dc6` vs TP-0002/0004 `2e346e20` (3.9MB, 262 rows) | BOUNDARY §8; C-D1-02 | RESOLVED per BOUNDARY: 2e346e20 accepted; root cause (project_root variation) OPEN_PENDING |
| K-04 | jpicklyk = AUTHORITY (TP-0004) vs PROJECTION/WORK_GRAPH_SURFACE (spec+TP-0001/0002) | BOUNDARY §8; C-D1-03 | RESOLVED by scope disambiguation (authoritative for own graph; projection from DCP's view) — both true |
| K-05 | S3→S1 `server.py` subprocess.Popen spawn exists vs TP-0004 "no bridge between jpicklyk and FastAPI" | C-D1-04; BOUNDARY §8 | OPEN_PENDING (PARTIALLY RESOLVED): source spawn confirmed; data-bridge unobserved; **compose runtime status UNKNOWN — do not declare independent until inspected** |
| K-06 | Decision #132 "skip jpicklyk" vs runtime (AGENTS.md §6 + .mcp.json designate it authority) | C-D1-05 | RESOLVED: #132 HISTORICAL/SUPERSEDED |
| K-07 | `computed_at`: adapter-schema.md says `float` vs code says `str`/ISO-8601 | C-D1-06 | UNRESOLVED — code authoritative; doc needs update |
| K-08 | `integration.loaded_from`: doc 2 values vs code 4 values | C-D1-07 | UNRESOLVED — code authoritative |
| K-09 | "Adapter obtains series state without external dependency" vs `from_series_id` requires absent `.dopetask/series/<id>/state.json` | C-D1-08 | OPEN_PENDING — acquisition strategy undefined |
| K-10 | Two status vocabularies: `TaskStatus` (ADHD) vs `PacketState` (lease lifecycle), no mapping | C-D1-10 | OPEN_PENDING — DCP render must handle both |
| K-11 | `/info` declares MCP SSE `/sse` (37 tools) vs no `@app.get("/sse")` in audited routes | C-D1-11 | OPEN_PENDING — may be FastMCP ASGI mount |
| K-12 | `conport_insight_publisher.py` direct aiohttp to ConPort vs DopeconBridge everywhere else | C-D1-12 | OPEN_PENDING — two write paths; DCP must not assume single-path |
| K-13 | S3 ConPort sync fire-and-forget (`asyncio.create_task` w/o await, `task_coordinator.py:306`); data may be lost on exit | C-D1-13 | OPEN_PENDING — "ConPort is durable path for S3" is overstated; sync best-effort |
| K-14 | Duplicate isolated `InMemoryPMTaskStore` (coordinator vs dopecon-bridge emitter), no cross-process sync | C-D1-14 | OPEN_PENDING — may diverge silently; no single coherent PM task state |
| K-15 | "Redis present → execution state durable" | C-D1-15 | RESOLVED (refuted): Redis confined to event_coordinator.py + adhd_engine.py; NOT ExecutionStore/PMTaskStore — assumption must be explicitly blocked |
| K-16 | DCP spec lists "dry-run available" as adapter-boundary condition vs no native `--dry-run` in v0.5.1 | C-D1-16 | OPEN_PENDING — dry-run via pre-captured artifacts only, not a dopetask flag |
| K-17 | `DopetaskPacketLauncher`/`SequentialPlanRunner` co-located in adapter dir but are EXECUTOR | C-D1-CROSS | RESOLVED in packets: classify as EXECUTOR; co-location is NOT a safety signal |
| K-18 | "Single unified PROOF.json contract" vs 5 incompatible shape families | D2 §5.1; PROOF-0001 | RESOLVED (overturned): shape-family dispatch required |
| K-19 | PR #758 MERGED (OPENPRS-0001) vs TP-102 CLI files ABSENT in working tree (ACTION-0001) | C-1; D2 §10 | **UNRESOLVED — branch HEAD difference; verify against `main`, not feature branch** |
| K-20 | Embedded-audit `status` (outcome) vs orchestrator `status` (lifecycle) — same name, orthogonal axes | C-2 | PRESERVED — DCP must not conflate |
| K-21 | "PR Steward advisory-only" generalization vs `queue_drain.py:2017` live `gh pr merge execute=True` | C-3 | RESOLVED on framing: tools/pr_steward=advisory; pr_merge_specialist=mutation-capable — two-layer distinction REQUIRED |
| K-22 | `PROOF.json route_behavior=SANDBOX_BLOCKED` vs `PAL_CLINK_AUDIT_OUTPUT return_code=0` (run succeeded) | C-4 | PRESERVED — PROOF.json stale; machine consumers would conclude failure when it passed |
| K-23 | Three freshness vocabularies (proof_freshness / freshness_state / CHECKSUMS.sha256) for "is proof current?" | C-5 | PRESERVED — DCP must pick one model + declare it |
| K-24 | `noninteractive_mode_proven=True` (config-level) vs DR-004 "Claude CLI only soft/policy RO" | C-6 | PRESERVED — naming misleading; treat as config-level only, not runtime-verified |
| K-25 | DR-002 launch-blog "Copilot cannot mutate existing PR branch" vs current docs "Copilot pushes to PR branch by default" | ACTION-0001 §8 | PRESERVED — current docs win; DCP must NOT assume Copilot read-only in GitHub context |
| K-26 | PAL clink: external UNKNOWN (DR-004) vs repo-observable (`pal_clink.py`) | C1 (D5); AUDIT-0001 | **PRESERVED — not reconcilable from external alone; configuration=AVAILABLE, execution=NEEDS_SUPERVISOR; do not upgrade to KNOWN on DR-004 alone** |
| K-27 | Proof version: DNHART "v1" (`proof-schema.dnh-crm-v1.json` canonical) vs RED_LANE "1.2" (`PROOF_CONTRACT_VERSION="1.2"` in `bundle.py:25`; v1 file ABSENT from current checkout) | RED_LANE §8 C1; DNHART §8 C1 | **PRESERVED — runtime tips to 1.2; v1 file exists on `rdcp/bootstrap-evidence` branch; do NOT use "v1" in DCP artifacts until alignment confirmed** |
| K-28 | dopecon-bridge "single authority point" (README) vs TRANSPORT_ONLY (routes.py header + manifest) | MEMCTX §8 C2 | PRESERVED — runtime+manifest override; README is doc drift; DCP must not inherit claim |
| K-29 | ConPort relationship authority: cross-system-synthesis doc assigns ConPort vs SYSTEM_ConPort.md says no write API proven | MEMCTX §8 C4 | PRESERVED — AUTHORITY for traversal/query; relationship WRITE = UNKNOWN |
| K-30 | ConPort runtime CONFLICTING: `enhanced_server.py` (3004) vs `src/conport/memory_server.py` — deployed primary unresolved | MEMCTX §8; D3 §8.5 | **PRESERVED (CONFLICTING) — do not collapse without live deployment resolution** |
| K-31 | dope-memory runtime: `dope_memory_main.py` (3020 active) vs `mcp_stdio_adapter.py` (legacy 8096) | MEMCTX §8; D3 §8.5 | PRESERVED: 3020 active, 8096 deprecated — do NOT use 8096 |
| K-32 | task-orchestrator module: legacy `task_orchestrator/app.py` vs active `services/task-orchestrator/app/main.py` | D3 §8.5; AGENTS.md §10 | PRESERVED (CONFLICTING per AGENTS.md §10) — runtime inspection of compose context needed |
| K-33 | DR-011 classification: REFERENCE_ONLY/advisory (XPROJ §4) vs "upgrade to VERIFIED_BY_PROOF / authoritative template" (XPROJ §11) | D3 §9.6 | PRESERVED — existence=OBSERVED; authority TIER stays advisory; validate each field vs runtime |
| K-34 | dNh red-lane count "12" framing vs 11 confirmed + 1 probable (WhatsApp) from §4.3 | D3 §7.1 | PRESERVED — WhatsApp status UNKNOWN; not in §4.3; confirm before classifier finalized |
| K-35 | Lane-count framing 7 generic/8 Dopemux vs ~8 generic/7 Dopemux enumeration; lane overlap (generic policy + project-specific runtime) | D3 §7.3 | PRESERVED — membership lists authoritative over totals; overlap is real tension not dedup error |
| K-36 | `gemini-dispatch.yml` `pull-requests:write` (GHA layer) vs T5-gate (orchestrator layer) | D3 §7.2 C3 | PRESERVED — GHA grants capability; orchestrator enforces policy; neither overrides the other |
| K-37 | COCKPIT-0001 internally inconsistent: §3 VERIFIED_BY_PROOF (pack MERGED to main, 2026-06-03) vs §7/§9 STALE (pack not merged, 2026-05-02) | CONTRA-01/06 | PRESERVED — VERIFIED_BY_PROOF wins (pack IS on main); packet is NOT uniform-authority; code-merged ≠ design-cleared |
| K-38 | "Palette" = two things: `ui-dashboard/` ADHD dashboard (DCP-separate per COCKPIT-0001) vs `out/cockpit-command-palette/` (DCP-internal); CURRENT-0001 calls web Palette "a second cockpit surface" | CONTRA-03 | **PRESERVED — unresolved between packets; synthesis must decide web-Palette scope** |
| K-39 | neon_dashboard vs governed cockpit: both Textual apps; no explicit deprecation record for neon_dashboard | D4 §8.2 | PRESERVED — COCKPIT-0001's "governed cockpit is the one" is PROPOSED (stated in packet), not a decision record |
| K-40 | TP count: 93 (INV-0000) vs 91 (INTENT-0001, direct file count) | CONTRA-02 | PRESERVED — use 91 operative; note discrepancy |
| K-41 | Proof-bundle count: "9 bundles" vs ~13 IDs listed in same INTENT-0001 §3 cell | CONTRA-04 | PRESERVED — minor internal discrepancy; OPEN_PENDING applies regardless |
| K-42 | MCP config drift: `mas-sequential-thinking` referenced in `task-master-mcp-config.json` despite deprecation (claude.md → PAL) | CONTRA-05; TOOLING §8 | PRESERVED — incomplete migration; audit config + docs before asserting loaded MCP |
| K-43 | Chronicle field count: DR-014 "~22 fields" vs DR-016 "~24 fields" | C2 (D5) | PRESERVED — DR-016 later/authoritative (~24); not a contradiction, a draft evolution; preserve delta |
| K-44 | Gemini CLI → Antigravity cutover 2026-06-18 (15 days out at evidence date) | C5 (D5) | PRESERVED (date-sensitive UNKNOWN) — whether auditor-router config needs update post-cutover; flag AUDIT-0001 recheck after 2026-06-18 |
| K-45 | DR-013 fail-closed: `DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md` flagged as prerequisite but NOT produced | C4 (D5) | PRESERVED — carry as known gap; do not fabricate or pretend produced |
| K-46 | `LIVE_WRITE_READY` referenced as gate but UNDEFINED anywhere (rg → 0) | TP-0004; multiple | OPEN_PENDING — master gate must be defined+proven before any live TO write |

---

## 12. Architecture Options To Compare

The real options GPT-5.5 must weigh, framed from the evidence. Each carries the evidence pull and the constraint walls. **These are options to compare, not recommendations.**

### O-1. Where DCP Core lives
- **(a) New `dopemux dcp` CLI namespace** (owns evidence/readiness/proof/action-planning; consumes other surfaces as adapters). DR-011 steer: DCP ≈ Backstage+OPA+provenance-verifier+thin action-broker, NOT a runtime engine. DR-010 MVP: CLI primary.
- **(b) Adopt/consume the existing governed TUI cockpit stack** (`src/dopemux/ui/cockpit/`, on main, guarded) as the DCP surface.
- Evidence pull: cockpit PM slice already merged + guarded; DR-010/011 say CLI/catalog-first; spec §8 explicitly asks "DCP Core location (+ consume current cockpit/TUI stack or own new CLI namespace?)".

### O-2. TO posture (the spec's "split answer")
- jpicklyk (S1) = projection/work-graph target; FastAPI (S3) = optional cockpit/coordination bridge; neither = Core; Dopetask (S4) = execution/proof adapter. Sub-option: jpicklyk **project from** (dry-run renderer) vs **merely observe** (read-only status, no projection model). LIVE_WRITE_READY UNDEFINED forces dry-run-only regardless. GATE-EXT-2: live writes only behind proven three-lane contract.

### O-3. Dopetask as spine — yes / no / partial
- Evidence: mature read-adapter stack (9 modules, zero-subprocess) + EXECUTOR surfaces (launcher/runner) that DCP must never instantiate. Spec §8: "Dopetask = likely execution/proof adapter not full plane." Partial = consume proof bundles via adapter, never invoke execution. No series state exists today (CLAIMED_ONLY).

### O-4. Generic vs project-specific architecture
- DR-015 packaging: `dcp-core` + `dcp-profile-dopemux` + `dcp-profile-dnh-crm` + repo-local evidence (extend via rules/schemas/path-maps, not forked prompts; repo-local must not weaken core denies). Evidence: Dopemux (split-authority, governance-level red lanes, no runtime classifier) and dNh (event-sourced, file-path-anchored classifier, 11+1 lanes) are fundamentally asymmetric — generic CONTROL_SNAPSHOT envelope + per-project extension blocks (D3 §9.2). Generic red lanes vs Dopemux-specific vs dNh-specific (§7).

### O-5. Cockpit MVP — adopt / wrap / ignore the existing TUI + Palette
- **Adopt**: governed TUI PM slice becomes DCP cockpit MVP. **Wrap**: DCP CLI/artifacts primary, TUI as optional read-only projection (DR-010 ordering). **Ignore**: artifact+CLI only, defer all TUI.
- Constraints: all cockpit TP design-gating still `safe_for_claude_design:"NO"`; new wave (#731–749) on feature branch only; web Palette scope unresolved (K-38); DR-010 "risk panel not green-badge theatre" + authority badges + unknowns-as-first-class.

### O-6. Memory adapter family — writes in v1? (y/n)
- DR-014: V1 = READ-ONLY across all adapters **except an optional DCP-owned append-only chronicle namespace**. MEMCTX-0001: DCP v1 = READ/EXPORT/POINTER only across all five systems. Option: pure read-only v1 vs read-only + DCP-owned append-only chronicle. dope-memory authority class + ConPort relationship-write API are UNKNOWN (cannot assume write).

### O-7. Tooling layer — build after contracts
- DR-015 `BUILD_AFTER_CORE_CONTRACTS`: lock red-lane taxonomy / receipt schema / mutation classes / approval artifact / project path+resource maps FIRST. Then split: which surfaces → DCP Claude plugin vs skills vs deterministic hooks vs `dopemux dcp` CLI; advisory vs blocking hooks; how dNh red-lane hooks differ from Dopemux (file-path-anchored vs governance-level). Plugin v1 `defaultEnabled:false`. Existing infra at scale (10 hooks, 12 guards, 80 personas, etc.) with UNKNOWN integration.

### O-8. Proof representation
- Option A (adopt RDCP `PROOF_POINTER.json` + extend), B (new `DCP_PROOF_POINTER.json` combining RDCP + PR-Steward freshness), C (shape-family dispatcher). Must account for 5 incompatible shape families + 30+ existing PROOF.json (no retroactive migration) + DR-005 compose-existing-standards + auditorVerdict≠validationState. Evidence supports B or C.

### O-9. Autoreview / PR-merge stack — adopt / quarantine / mine
- Largest surface, entirely CLAIMED_ONLY (DMX-AUTOREVIEW-PLATFORM + pr_merge_specialist). `steward_gate.py` ABSENT; merge seam unguarded; 25 open PRs no proof bundles. Spec §8 new decision. Options: adopt as DCP authority / quarantine as Dopemux-specific / mine for patterns. DR-012 role-separation forbids self-certifying loops.

---

## 13. Hard Unknowns

Carried from the evidence without resolution. **Marking UNKNOWN is the correct state — never upgrade to fact.**

| Unknown | Blocks | Source |
|---|---|---|
| **`LIVE_WRITE_READY` prerequisites** — undefined anywhere (rg → 0); no code gate/flag/contract | Any live TO write authorization | TP-0004; BOUNDARY §1; XPROJ §7 |
| **Split-brain TO state**: canonical workspace dir + active hash root cause (project_root path variation) | Reliable jpicklyk projection; canonicalizing TASK_ORCHESTRATOR_PROJECT_ROOT | K-02/K-03; BOUNDARY §7 |
| **S3→S1 `server.py` coupling in compose** — subprocess.Popen in source, absent from Dockerfile COPY | Declaring S1/S3 independent | K-05; BOUNDARY §1 |
| **Branch-protection state (both repos)** — `enforce_admins=false`; ruleset advanced conditions need admin scope; dNh branch protection state UNKNOWN | Gated-PR-process implementation; TP-DNH-RDCP-0023/0024 | GITHUB-0001 §7; RED_LANE §7; XPROJ §7 |
| **CODEOWNERS enforcement actually active** (single `@hu3mann`) | Whether review enforcement is real | GITHUB-0001 §7 |
| **`queue_drain.py execute=True` production-reachability** — call graph from CLI to execute=True not traced | Whether PR-merge domain is safe to wire | PR-0001 §7; OPENPRS-0001 |
| **dNh proof-schema location/contents** — `proof-schema.dnh-crm-v1.json` absent from current checkout (on bootstrap branch); `proof-schema-dnh-crm-v1.json` lives in dNh_CRM repo | Proof Adapter implementation; proof version alignment | K-27; PROOF-0001 §7; DNHART §8 |
| **RAG worker write-lane status (dNh)** — `rag_worker.lock` dirty (likely running) | RAG lane active-vs-draft classification | RED_LANE §7; XPROJ §3 |
| **OpenClaw active runtime status (dNh)** — naming constant, not confirmed live process | Browser/CDP lane classification | RED_LANE §4/§9 |
| **WhatsApp outbound (probable dNh 12th lane)** — imported but not in §4.3 enumeration | dNh red-lane classifier finalization | K-34; RED_LANE §8 C2 |
| **dNh task graph presence** — no task-orchestrator.py / work_items.db found; TP-DNH-RDCP-0026 BLOCKED | dNh task_graph adapter cell | XPROJ §3/§7 |
| **ConPort relationship WRITE API** — no write API proven (traversal/query only) | ConPort relationship authority scope | K-29; MEMCTX §8 C4 |
| **dope-memory authority class + write semantics** — authoritative / append-only / mutable / projection? | Memory adapter contract | D5 §11; MEMCTX |
| **ConPort + task-orchestrator deployed-primary** (CONFLICTING runtime surfaces) | Which endpoint DCP reads | K-30/K-32; D3 §8.5 |
| **Auditor binary presence + auth** (claude-audit/gemini-audit/AGY) — static-only, no live probe | Auditor execution axis | AUDIT-0001 §7 |
| **Antigravity↔Gemini cutover impact (2026-06-18)** | Auditor-router config currency | K-44 |
| **Dopetask series-state acquisition strategy** — undefined (3 options) | Consuming series state via adapter | K-09 |
| **Tooling integration**: persona routing / skill instantiation / MCP config currency / hook runtime faithfulness / pre-commit bypass | Tooling standardization decisions | TOOLING §7/§8 |
| **Cockpit timeline source** — artifacts-first vs dope-memory/chronicle-first (not yet decided) | Cockpit data-source architecture | checklist #4; DR-014 |
| **`DCP_PRE_SYNTHESIS_CONTRADICTION_LEDGER.md`** — NOT produced by DR campaign | Treat as not-yet-produced | K-45; DR-013 |

---

## 14. Required GPT-5.5 Decisions

The v2 §8 decision set (10 updated + 3 new = 13) PLUS the 8 lifted COMPRESS checklist items, **deduplicated**. Overlapping decisions are merged into a single row and the overlap is noted, so each row below is one distinct decision. **Total distinct decisions: 16** (the 13 §8 items collapse to 10 rows — §8-#2+#12→D2 and §8-#10+#13→D10 each merge two §8 items — plus 6 NEW checklist items → D11–D16; checklist #5 and #6 fold into D5/D6 with no new row).

> **De-dup map**: checklist #5 (cockpit MVP) ≡ §8-#5/§8-#11 → merged at **D5**. checklist #6 (automation ladder) ≡ §8-#6 → merged at **D6**. The other 6 checklist items (#1 memory split, #2 chronicle receipt, #3 retrieval source-trace, #4 cockpit timeline source, #7 tooling boundaries, #8 mirrors/proxies) are NEW and become **D11–D16**. §8-#12 (jpicklyk project-vs-observe) folds into **D2**. §8-#13 (autoreview adopt/quarantine/mine) → **D9**.

| ID | Decision | Source | Key constraint / evidence |
|---|---|---|---|
| **D1** | **DCP Core location** — new `dopemux dcp` CLI namespace vs consume existing cockpit/TUI stack | §8-#1 | DR-011 (DCP≈Backstage+OPA+verifier+broker, not runtime engine); DR-010 (CLI-first); O-1 |
| **D2** | **TO posture (split answer)** — jpicklyk=projection/work-graph (project-from vs merely-observe); FastAPI=optional cockpit/bridge; neither=Core; live writes only behind three-lane contract | §8-#2 + §8-#12 | LIVE_WRITE_READY UNDEFINED → dry-run only; GATE-EXT-2/3; BOUNDARY DECISION; O-2 |
| **D3** | **Dopetask scope** — execution/proof adapter not full plane (consume bundles via read-adapter; never invoke execution) | §8-#3 | EXECUTOR surfaces must never be instantiated; no series state today; O-3 |
| **D4** | **Generic vs project-specific** — incl red-lane split (generic/Dopemux/dNh) + dNh artifact reuse; `dcp-core` + per-project profiles | §8-#4 | Dopemux/dNh asymmetry; DR-015 packaging; CONTROL_SNAPSHOT envelope + extension blocks; O-4 |
| **D5** | **Cockpit MVP** — adopt existing governed TUI vs wrap (TUI read-only projection) vs ignore (artifact+CLI only); evaluate TUI + Palette | §8-#5 + §8-#11 + checklist #5 | All TP gating `safe_for_claude_design:NO`; new wave on feature branch only; DR-010 risk-panel/badges; web-Palette scope unresolved (K-38); O-5 |
| **D6** | **Automation ladder (L0–L7 + NEVER)** — what's safe in v1 vs supervisor-gated; automate-first set = evidence-compression/prompt-gen/proof-verify/next-action/dry-run-projection | §8-#6 + checklist #6 | DR-010 (automate detection/summarization/proof/watch/route-suggestion; keep manual live-writes/approval/merge); UX targets DEFERRED; O-7 |
| **D7** | **First build packet** — TBD post-evidence/post-synthesis | §8-#7 | Sequencing decision; depends on D1–D6 |
| **D8** | **Dry-run set** — live TO writes / Dopetask exec / GitHub mutation / dNh runtime / PR repair all dry-run until proof | §8-#8 | spec §1 forbidden set; GATE-EXT-2/6/7; all surfaces dry-run by default |
| **D9** | **Proofs generic representation** — must account for 5 existing shape families + strict-schema warnings; Option A/B/C | §8-#9 | shape-family dispatch; pointer-first; auditorVerdict≠validationState; no retroactive migration; O-8 |
| **D10** | **Universal red lanes + 4 hazard classes** — AI-agent-authority-collapse, cockpit-hidden-risk, live-write-receipts, external-product-drift; PLUS autoreview stack adopt/quarantine/mine | §8-#10 + §8-#13 | role-separation (DR-012); largest CLAIMED_ONLY surface; steward_gate ABSENT; O-9 |
| **D11** | **Memory split** — what belongs in ConPort vs dope-memory vs dope-context? Does DCP write to them in v1 (likely export-only)? | checklist #1 | DR-014 (V1 read-only except DCP-owned chronicle); MEMCTX (READ/EXPORT/POINTER only); dope-memory class UNKNOWN; O-6 |
| **D12** | **Chronicle receipt model** — event types + required fields (event_id/type, project_id, series_id, tp_id, source_sha, artifact_refs, proof_refs, actor, tool, timestamp_utc, authority_label, red_lanes, supersedes). Receipt model, NOT runtime-command model | checklist #2 | DR-016 ~24-field Chronicle-Receipt spec; chronicle append-only via mcp-capture gateway; field-name vocab UNKNOWN (repo-local) |
| **D13** | **Retrieval source-trace** — every hit carries source path/system/SHA-or-freshness/authority-tier/timestamp/confidence/derived?/canonical-writer. "No spooky search authority" | checklist #3 | DR-016 17-field Evidence-Hit spec; `complexity` NOT in dope-context search return; authority_tier ⊥ confidence; four freshness clocks |
| **D14** | **Cockpit timeline source** — artifacts-first vs dope-memory/chronicle-first | checklist #4 | DR-014 (cockpit=projection-only, must badge); source not yet decided (UNKNOWN) |
| **D15** | **Tooling boundaries** — what belongs in a DCP Claude plugin vs skills vs deterministic hooks vs `dopemux dcp` CLI; advisory vs blocking hooks; how dNh red-lane hooks differ from Dopemux | checklist #7 | DR-015 BUILD_AFTER_CORE_CONTRACTS; block>ask>warn>allow; client hooks bypassable→CI; dNh file-path vs Dopemux governance-level; O-7 |
| **D16** | **Mirrors/proxies** — how DCP avoids treating dopecon-bridge proxy routes / index freshness as source truth | checklist #8 | dopecon-bridge TRANSPORT_ONLY (README overclaim K-28); cache-freshness≠source-freshness; mirror-as-authority anti-pattern (DR-014) |

---

*End of DCP 5.5 Synthesis Input Pack. Assembled read-only from D1–D5 + BOUNDARY + CAMPAIGN_PROGRESS + DCP_CAMPAIGN_SPEC_v2 + DR ledger. Repo runtime outranks external DR throughout. Contradictions preserved (46 rows, §11). Required decisions (16, §14). This pack is INPUT to GPT-5.5 synthesis, not the architecture decision.*
