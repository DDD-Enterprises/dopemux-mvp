# Cross-Repo Boundary Inventory — Dopemux Task-Orchestrator Integration

> Generated 2026-05-25. Consolidator across 4 peer repos.
> Baseline: this repo's `AGENTS.md` (159 lines) and `ARCHITECTURE.md` (196 lines).
> Per-repo files live at the root of each peer; see links in §1.

## 1. Summary

| # | Peer | Recommended Use | Owned Runtime | Key Interfaces | Drift Severity | Per-repo file |
|---|---|---|---|---|---|---|
| 1 | [dopeTask](../../dopeTask/CROSS_REPO_INVENTORY.md) | **ACTIVE_DEPENDENCY** | Task execution kernel; Task Packet validator; proof-bundle producer | `dopetask` CLI; `task_packet.schema.json`; proof bundle contract v1.0; adapter entry points | **none** on boundary; medium on schema naming (`dopetask-canonical-spec.json` vs `task_packet.schema.json`) | `/Users/hue/code/dopeTask/CROSS_REPO_INVENTORY.md` |
| 2 | [dNh_CRM](../../dNh_CRM/CROSS_REPO_INVENTORY.md) | **EXPERIMENTAL_ONLY** | CRM domain logic; local SQLite event spine; local proof bundle v1.2 | `dnh-crm` CLI; event store API; Telegram worker; Twenty CRM writeback | **medium** — proof contract v1.2 not synced with dopemux-mvp; ConPort/dope-memory/dope-context documented but not implemented | `/Users/hue/code/dNh_CRM/CROSS_REPO_INVENTORY.md` |
| 3 | [task-orchestrator](../../task-orchestrator/CROSS_REPO_INVENTORY.md) (Kotlin MCP server) | **ACTIVE_DEPENDENCY (operator caveat)** | Workflow state machine; 13 MCP tools; phase-gate enforcement | MCP tools via STDIO + HTTP transport; 26 contract schemas; `advance_item`/`get_context` core | **none** on boundary; medium on missing proof envelope; **naming collision** with this repo's internal `services/task-orchestrator/` | `/Users/hue/code/task-orchestrator/CROSS_REPO_INVENTORY.md` |
| 4 | [dope-arch-investigation](../../dope-arch-investigation/CROSS_REPO_INVENTORY.md) | **ADVISORY_REFERENCE** | none (investigation kit) | frozen audit reports (`docs/investigations/00–70`); governance gate flags; task packets (`PKT-*`); supervisor decisions | **high** — surfaces 8 S1 architecture blockers + 5 S0 governance blockers, all unresolved | `/Users/hue/code/dope-arch-investigation/CROSS_REPO_INVENTORY.md` |

## 2. Cross-Repo Drift Findings

Findings where claims conflict *across* peers or against this repo's `AGENTS.md` / `ARCHITECTURE.md`.

### 2.1 Naming collision: two distinct "task-orchestrator" systems

This repo's `services/task-orchestrator/` (Python "Coordination API", FastAPI + FastMCP, port 8000) and the standalone Kotlin MCP server at `/Users/hue/code/task-orchestrator` (`github.com/jpicklyk/task-orchestrator`) share a directory name but are **different codebases owned by different planes**. They are not two competing implementations; they are stacked.

- **Architectural relationship verified during this pass**: `services/task-orchestrator/server.py:103-148` (`start_orchestrator()`) builds a command (env-configured path → `docker run task-orchestrator:latest` → gradle wrapper → `java -jar /opt/task-orchestrator/task-orchestrator.jar --mcp-mode`) and runs it via `subprocess.Popen` at line 141. Line 155 is the FileNotFoundError fallback ("Clone from: https://github.com/jpicklyk/task-orchestrator"), which fires only when the JAR is missing — operator remediation guidance, not the active runtime path. `services/.claude/CLAUDE.md` confirms `task-orchestrator | 8000 | ADHD-aware task mgmt` in the service registry — port 8000 is the Python Coordination API; the Kotlin JAR is the spawned engine.
- **`AGENTS.md §10:135`'s** "conflicted across `app/main.py`, `task_orchestrator/app.py`, and Docker wiring" warning is about the **internal Python service**, where `task_orchestrator/app.py:10–13` hard-fails (`_hard_fail()`, `sys.exit(1)`) and `app/main.py` is canonical.
- The standalone Kotlin repo has its own deployment friction: `docker-compose.yml:5` default service `mcp-task-orchestrator` targets `runtime-v2` (deprecated). Operators must use `mcp-task-orchestrator-current` or `--profile current` to get v3. This is in-repo cleanup, not an inter-repo conflict.
- **Resolution needed**: either rename one (e.g., rename the internal Python wrapper to `coordination-api`) or explicitly document the Python-wraps-Kotlin relationship in `AGENTS.md §6` and `ARCHITECTURE.md`. The collision currently makes a reader believe there are two competing implementations when there is actually one engine and one wrapper.

### 2.2 Version pin mismatch on dopeTask

From `dope-arch-investigation/09-integration-risk-register.md R-02`:

| System | Pinned dopeTask version |
|---|---|
| this repo (dopemux-mvp) | `0.5.1` (historical) |
| `/Users/hue/code/dopeTask` self | `0.5.7` (per `pyproject.toml:6`) |
| dope-agent (per investigation) | `0.5.7` |

S1 blocker. Either this repo's pin needs to bump to `0.5.7`, or dopeTask needs to confirm 0.5.1 → 0.5.7 is backward compatible. **Action**: reconcile pin in this repo's dependency manifest (path: TBD, follow-up).

### 2.3 Task Packet schema naming

- `AGENTS.md §5:55`: "Task Packets must conform to `dopetask-canonical-spec.json` when that schema is available."
- `/Users/hue/code/dopeTask` ships `dopetask_schemas/task_packet.schema.json` and `task_packet.strict.schema.json`.
- The filenames differ. **Status**: unclear whether `dopetask-canonical-spec.json` is a separate aspirational filename, or whether `AGENTS.md §5` is referring to `task_packet.schema.json` by an older name. Reconcile.

### 2.4 Proof contract divergence

| System | Proof contract version | Surface classes? | Verified against this repo's `§9` |
|---|---|---|---|
| dopeTask | v1.0 (per `PROOF_BUNDLE_CONTRACT.md`) | no | yes — all 13 `AGENTS.md §9` fields covered |
| dNh_CRM | v1.2 (per `bundle.py:20–35`) | yes (`transitional_artifact`, `runtime_state_snapshot`, `sqlite_event_export`) | no — `§9` does not specify a contract version or surface classes |
| task-orchestrator (Kotlin) | n/a — only `metadata.timestamp` + `metadata.version` | no | no — no formal proof envelope |

dNh_CRM has *added* schema specificity that this repo's `AGENTS.md §9` does not mention. dopeTask is aligned. task-orchestrator (Kotlin) has a gap. **Action**: decide whether to (a) lift dNh_CRM's classification into the `§9` baseline, or (b) treat dNh_CRM's v1.2 as a local extension and document the divergence.

### 2.5 Ledger duality (no reconciliation protocol)

From `dope-arch-investigation R-12` (S0):

Three ledger surfaces with no documented reconciliation:

1. dopeTask `SERIES_STATE.json` (per-series authoritative)
2. dope-agent mirror (investigation finding; not reverified here)
3. this repo's chronicle.sqlite + ConPort (PostgreSQL AGE)

`AGENTS.md §6:81–82` and `ARCHITECTURE.md §3.4:54–61` correctly state ConPort and dope-memory are separate authorities, but the reconciliation protocol between dopeTask's series state and this repo's ledgers is not specified.

### 2.6 NW clause sourcing + TaskPacket shape mismatch

From `dope-arch-investigation R-03` and `R-06` (S0/S1):

- `NW-001..NW-016` clauses appear in dopeUI but have no traced canonical source in this repo. Per `AGENTS.md §7`, these are advisory until runtime/source supports them.
- dopeUI's TaskPacket schema does not match dopeTask's canonical shape, which would block dopeUI → dopemux → dopeTask packet flow.

Not directly verified in this pass (dopeUI was out of inventory scope), but flagged for the next supervisor decision.

### 2.7 dNh_CRM documents but does not implement dope-* consumption

`dNh_CRM/GEMINI.md:18–58` documents ConPort, dope-memory, dope-context as integration targets. The branch name (`governance-doctrine-integration`) signals intent. But active `src/` has no ConPort HTTP client, no dope-memory writes, no dope-context queries. Proof bundles stay local. **Risk**: if any service in this repo expects dNh_CRM proof outputs in ConPort/dope-memory, the handoff is undocumented and unimplemented.

## 3. Integration Recommendations

For each peer:

### 3.1 dopeTask — promote to ACTIVE_DEPENDENCY

- It is the canonical task-execution runtime referenced by `AGENTS.md §6:78` and `ARCHITECTURE.md §3.2`.
- Schema and proof contract are published; no boundary overreach.
- **Friction to clear**: version pin (2.2), schema-name reconciliation (2.3).

### 3.2 dNh_CRM — keep as EXPERIMENTAL_ONLY (reference impl, not a dependency)

- Use as a reference implementation of event-sourcing + proof patterns.
- **Do not** treat as a dopemux-mvp client surface until ConPort write paths are implemented and proof contract v1.2 is reconciled with `§9`.

### 3.3 task-orchestrator (Kotlin) — ACTIVE_DEPENDENCY with operator caveat

- Spawned as a subprocess by this repo's Python Coordination API (`services/task-orchestrator/server.py:103-148`). Dependency is exercised at runtime, not aspirational.
- Single canonical Kotlin entrypoint; 13 MCP tools; phase-gate enforcement working.
- **Friction to clear**:
  - Fix `docker-compose.yml:5` default service in the Kotlin repo to target `runtime-current`, OR add a deployment doc.
  - Add a formal proof envelope to `advance_item.response.schema.json` to satisfy `§9`.
  - Resolve the directory-name collision with the internal Python wrapper (§2.1).

### 3.4 dope-arch-investigation — keep as ADVISORY_REFERENCE

- Use as evidence baseline for the next supervisor decision.
- Resolve the 5 S0 governance blockers (R-08, R-10, R-11, R-12, R-13) before implementation gates open.
- Cross-validate findings against current source before adopting any proposal (NW clauses, schema shapes).
- Staleness signal: last supervisor decision is file 32 (2026-05-13). If material changes have landed in dopemux-mvp/dopeTask since then, re-audit.

## 4. Open UNKNOWNs

Boundary questions this inventory could not resolve. Each requires user/maintainer input or follow-up investigation.

1. **dopetask-canonical-spec.json vs task_packet.schema.json** — same artifact under different names, or two different files? (`AGENTS.md §5:55` vs `dopeTask/dopetask_schemas/`)
2. **dopeTask version pin** — does dopemux-mvp still pin 0.5.1? Where is the manifest? (Cross-ref R-02.)
3. **Internal Python `services/task-orchestrator/` retention policy** — should the dual-runtime conflict (`§10:135`) be fixed by deleting `task_orchestrator/app.py` (the hard-failing stub), or is it intentionally retained as a tripwire?
4. **dNh_CRM proof handoff** — is dNh_CRM expected to forward its v1.2 proof bundles into ConPort/dope-memory? If yes, when? If no, document divergence.
5. **dopeUI presence** — investigation references dopeUI extensively (`NW-001..NW-016`, schema shape mismatch) but the dopeUI repo was not in this inventory scope. Should it be in a follow-up pass?
6. **dope-agent presence** — same: `dope-agent-system` (and several ChatRipperXXX/Dopemux-ChatRipperXXX variants) were classified as LIKELY_PEERs in triage but deferred. Each may own a slice of this repo's authority surface.
7. **Acceptance authority** — `dope-arch-investigation R-13` flags that no record-level signer separation exists. Who owns acceptance? `AGENTS.md §9:110–130` defines proof contents but does not name the authority.

## 5. Methodology

- Triage scan of `/Users/hue/code` enumerated 10 LIKELY_PEER and 2 POSSIBLE_PEER repos.
- Top 4 selected for inspection: dopeTask, dNh_CRM, task-orchestrator, dope-arch-investigation.
- Each peer inspected by an Explore agent with the dopemux-mvp `AGENTS.md` + `ARCHITECTURE.md` baseline embedded in its prompt. Output schema: 8 sections (Identity, Runtime Ownership, Interfaces, Integration Role, Proof/Receipt/Handoff, Drift, Recommended Use, Evidence Ledger).
- Spot verification of `dopemux-mvp/services/task-orchestrator/{app/main.py, task_orchestrator/app.py}` confirmed §2.1's naming-collision finding directly in source.
- Read-only throughout. No peer-repo files were modified.

## 6. Out of Scope (Deferred)

Inspection of these LIKELY_PEERs was deferred:

- `ChatRipperXXX` + `Dopemux-ChatRipperXXX` — sibling forks; MCP-protocol testing presence
- `adOps` — fresh dopemux integration; litellm adapter
- `chatGPTexport`, `dope-agent-system`, `dopeTmux`, `openclaw_marketplace_agent_docs`
- `gpt-researcher` (POSSIBLE_PEER, older activity, ConPort-aware)

A follow-up pass should prioritize `dope-agent-system` (named in `dope-arch-investigation` as a primary subject) and one of the ChatRipper variants to validate MCP-protocol compliance against task-orchestrator's 26 schemas.

---

**Inventory authored**: Claude Code cross-repo boundary inventory pass, 2026-05-25.
