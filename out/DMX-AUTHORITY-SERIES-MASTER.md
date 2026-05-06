## 1. Executive verdict

**Verdict:** Dopemux is **plan-ready but not execution-verified** from this upload set. The architecture is usable only if every agent keeps authority split by domain. The repo is a composed workspace, not a unified platform, despite humanity’s tragic urge to name five services “memory” and then act surprised. 🧯

**Core truth:** `dopemux` is the operator control plane; external `dopetask` performs execution after handoff; PM is split across Leantime, task-orchestrator, ConPort, and dope-memory receipts; memory/retrieval are split across dope-memory, ConPort, and dope-context; dopecon-bridge is transport/proxy glue, not authority. The project docs explicitly warn that the repository does not prove a fully aligned single architecture. 

**P0 hazards:**

| Hazard                             | Why it matters                                                                        | Required action                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Task-orchestrator runtime conflict | Active code, Docker launch path, and ports disagree.                                  | Verify runtime, then reconcile Docker/compose/registry/docs.             |
| ConPort canonicality conflict      | Truth docs and system docs point to different active-looking runtime surfaces.        | Run runtime authority audit before any ConPort-dependent implementation. |
| Bridge authority illusion          | `/kg/*`, `/ddg/*`, and `/route/pm` look authoritative but are proxy/adapter surfaces. | Keep bridge-mediated writes tied to upstream canonical writers.          |
| Memory name/transport drift        | dope-memory lives under WMA tree; stale adapters still target old ports.              | Standardize docs, wrappers, and client defaults around active runtime.   |
| Agent authority unknown            | Multiple agent families exist with no proven canonical owner.                         | Treat agents as execution helpers only until authority is resolved.      |

**Execution readiness:** blocked until runtime verification packets run. The uploaded bundle contains truth docs and generated authority pointers, but not the live runtime code/config itself. So this output is implementation-ready **as a packet system**, not a claim that the repo was freshly executed here. Tiny difference, massive consequences. 🧪

---

## 2. What system actually is

Dopemux is a **multi-system operator/runtime workspace**. It contains an operator CLI, external execution handoff, PM adapters, workflow services, structured context, chronicle memory, retrieval indexing, bridge/proxy routing, ADHD/operator support, and repo-truth extraction. It is not a single application, not one “brain,” and not one canonical PM/memory/retrieval authority. 

| Plane            | Actual owner pattern                                                                                                                 | Not true                                                    |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| Operator/control | `dopemux` CLI coordinates startup, routing, MCP/service config, delegation.                                                          | `dopemux` is not PM, memory, retrieval, or execution truth. |
| Execution        | `dopemux → scripts/taskx → scripts/dopetask → external dopetask`.                                                                    | `taskx` is not a distinct runner.                           |
| PM               | Split by concern: Leantime metadata, task-orchestrator workflow, ConPort decision/progress/context, dope-memory historical receipts. | No single PM database is proven.                            |
| Memory           | dope-memory chronicle, ConPort structured context, WMA support snapshots.                                                            | “Memory” is not one system.                                 |
| Retrieval        | dope-context owns code/docs retrieval; ConPort owns structured/semantic context where implemented.                                   | Retrieval output is not source truth.                       |
| Bridge           | dopecon-bridge routes, proxies, adapts, transports events.                                                                           | Bridge is not task/workflow/decision/progress authority.    |
| Operator support | ADHD Engine maintains cognitive/operator-support state.                                                                              | It does not own PM or memory truth.                         |
| Extraction/audit | Repo Truth Extractor produces repo-truth artifacts.                                                                                  | It does not replace runtime truth.                          |

The rules file makes the core invariant explicit: planes are not services, services can span planes, authority is per domain, and bridge/proxy/retrieval/mirror surfaces must not be promoted into source truth. 

---

## 3. Source authority map

The uploaded set is a **documentation and contract bundle**, not a live runtime checkout. Runtime code remains first authority by policy, but runtime code was only represented through truth artifacts and pointer docs here. The upload set itself ranks core files, truth docs, system docs, PAL/TP docs, generated navigation, and adapter/proof contracts. 

| Files                              |                Class | Authority use                                                               | Status                                 |
| ---------------------------------- | -------------------: | --------------------------------------------------------------------------- | -------------------------------------- |
| `01_RULES.md`                      |       canonical docs | Governs truth hierarchy, worktree, PAL, safety, event/data/retrieval rules. | Promote                                |
| `02_PROJECT.md`                    |       canonical docs | Project shape and operating model.                                          | Promote                                |
| `03_ARCHITECTURE.md`               |       canonical docs | Multi-plane architecture extraction.                                        | Promote                                |
| `04_system-boundaries.md`          |       canonical docs | Boundary contract, but needs conflict tightening.                           | Promote after repair                   |
| `05_TRUTH_SCOPE.md`                |                truth | Scope/canonicality evidence.                                                | Promote, refresh                       |
| `06_TRUTH_SYSTEMS.md`              |                truth | System responsibility extraction.                                           | Promote, refresh                       |
| `07_TRUTH_INTERFACES.md`           |                truth | CLI/MCP/HTTP surface inventory.                                             | Promote, refresh                       |
| `08_TRUTH_DATA_EVENTS.md`          |                truth | Storage/event model evidence.                                               | Promote, refresh                       |
| `09_TRUTH_CANONICALS.md`           |                truth | Canonical runtime recommendations and conflicts.                            | Promote, refresh                       |
| `10_TRUTH_GAPS.md`                 |                truth | Drift, gaps, unresolved canonicality.                                       | Promote, refresh                       |
| `11_SERVICE_CATALOG.md`            |       canonical docs | Service tiering and status.                                                 | Promote after Tier 2 validation        |
| `12_PM_PLANE.md`                   |       canonical docs | PM read/write split and drift.                                              | Promote                                |
| `13_SYSTEM_Dopemux.md`             |          system docs | Dopemux system authority.                                                   | Promote after CLI failure verification |
| `14_SYSTEM_Dopetask.md`            |          system docs | External dopetask handoff authority.                                        | Promote                                |
| `15_SYSTEM_TaskOrchestrator.md`    |          system docs | Workflow authority and runtime drift.                                       | Promote after P0 fix                   |
| `16_SYSTEM_ConPort.md`             |          system docs | ConPort structured authority.                                               | Promote after conflict resolution      |
| `17_SYSTEM_DopeMemory.md`          |          system docs | Chronicle authority.                                                        | Promote                                |
| `18_SYSTEM_DopeContext.md`         |          system docs | Retrieval/index authority.                                                  | Promote                                |
| `19_SYSTEM_DopeconBridge.md`       |          system docs | Bridge/proxy boundary.                                                      | Promote                                |
| `20_SYSTEM_ADHDEngine.md`          |          system docs | Operator-support authority.                                                 | Promote with persistence gaps          |
| `21_SYSTEM_RepoTruthExtractor.md`  |          system docs | Extraction/audit runtime authority.                                         | Promote                                |
| `22_AGENTS.md`                     |   agent instructions | Operator safety rules for agents.                                           | Promote as agent policy                |
| `23_PAL_EXECUTION_RULES.md`        |   execution doctrine | Daily PAL execution rules.                                                  | Promote                                |
| `24_PAL_CHAINING_DOCTRINE.md`      |   execution doctrine | Full PAL sequencing doctrine.                                               | Promote                                |
| `25_PAL_PACKET_TEMPLATE.md`        |   execution template | Human packet template.                                                      | Keep                                   |
| `26_dopetask-cannonical-spec.json` |      contract/schema | Strict TP JSON schema.                                                      | Promote                                |
| `27_REPO_STRUCTURE.md`             |            generated | Navigation aid only.                                                        | Keep local / regenerate                |
| `28_SOURCE_AUTHORITY_MAP.md`       |            generated | Advisory source map.                                                        | Keep local / regenerate                |
| `29_TOP40_SELECTION_RATIONALE.md`  |            generated | Upload rationale.                                                           | Keep local / regenerate                |
| `30_DRIFT_AND_GAPS_SUMMARY.md`     |            generated | Upload drift summary.                                                       | Keep local / regenerate                |
| `31_RUNTIME_AUTHORITY_POINTERS.md` |            generated | Pointer list, not proof.                                                    | Keep local / regenerate                |
| `32_CHATGPT_PROJECT_UPLOAD_SET.md` |            generated | Upload strategy.                                                            | Keep                                   |
| `33_adapter-schema.md`             |             contract | Dopetask adapter JSON shape.                                                | Keep                                   |
| `34_adapter-contract.md`           |             contract | Dopetask adapter invariants.                                                | Keep                                   |
| `35_proof-bundle-schema.md`        |             contract | Proof bundle schema.                                                        | Promote                                |
| `36_proof-contract.md`             |             contract | Proof governance contract.                                                  | Promote                                |
| `37_handoff-contract.md`           |             contract | Skill handoff schema.                                                       | Promote                                |
| `38_TEMPLATE_TASK_PACKET.md`       |             template | Legacy/human-readable TP template.                                          | Keep, align with JSON schema           |
| `39_INDEX.md`                      | generated / registry | TP index, possibly stale.                                                   | Keep but validate before trusting      |
| `40_agents.instructions.md`        |   agent instructions | Copilot custom-agent guidance.                                              | Promote after current-doc check        |

**Top authority sources for this packet:** `01_RULES.md`, `05-10_TRUTH_*.md`, `02_PROJECT.md`, `03_ARCHITECTURE.md`, `04_system-boundaries.md`, `12_PM_PLANE.md`, `13-21_SYSTEM_*.md`, `23-26_PAL/TP/schema`, then generated upload/navigation docs. The source map also warns generated documents are advisory and should not replace exact source contents. 

---

## 4. Architecture extraction

| System                     | Owns                                                                                                             | Must not own                                                                                                      | Canonical runtime                                                                           |      Confidence | Open questions                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------: | --------------------------------------------------------------------------- |
| `dopemux`                  | CLI/operator control, startup, routing, MCP coordination, downstream delegation.                                 | PM truth, durable memory, retrieval truth, dopetask runtime, single agent authority.                              | `src/dopemux/cli.py`; console script from `pyproject.toml`.                                 | HIGH with drift | CLI import failure is reported in system doc and must be reproduced.        |
| `dopetask`                 | External task execution after handoff, TP lifecycle CLI.                                                         | PM, memory, retrieval, MCP lifecycle, routing, canonical state.                                                   | `scripts/dopetask` installs and execs pinned external binary; `taskx` shim only.            |            HIGH | Exact artifact schema inside external dopetask remains outside repo proof.  |
| Leantime                   | Passive PM metadata and project/ticket snapshots.                                                                | Workflow legality, decision/progress context, chronicle history.                                                  | External PM app via adapters/JSON-RPC clients.                                              |          MEDIUM | Leantime internals not repo-local.                                          |
| `task-orchestrator`        | Workflow transitions, workflow views, idea/epic workflow behavior, PM transition endpoints.                      | All PM state, passive metadata, chronicle, ConPort decision/progress/context, bridge authority.                   | `services/task-orchestrator/app/main.py` for active runtime code; packaging/ports conflict. |          MEDIUM | Docker launches hard-failing legacy module; port `8000` vs `3014`.          |
| ConPort                    | Structured decision/progress/context/custom-data surfaces.                                                       | PM metadata, workflow transition legality, chronicle, dope-context retrieval, bridge authority, universal memory. | CONFLICTING: Docker `enhanced_server.py` vs `src/conport/memory_server.py`.                 |          MEDIUM | Which runtime is deployed primary must be verified.                         |
| `dope-memory`              | SQLite chronicle ledger, work-log entries, raw event ingestion, replay/recap/correction/reflection/trajectory.   | PM state, ConPort structured memory, dope-context retrieval, upstream event authority, Postgres mirror authority. | `services/working-memory-assistant/dope_memory_main.py`, port `3020`, SQLite ledger.        |            HIGH | Native MCP transport not proven.                                            |
| `working-memory-assistant` | Snapshot/recovery and ADHD-adjacent support surfaces.                                                            | Canonical durable dope-memory authority unless proven.                                                            | `services/working-memory-assistant/main.py`, legacy/support.                                |          MEDIUM | Persistent writers unresolved.                                              |
| `dope-context`             | Code/docs indexing and retrieval; derived Qdrant/BM25/snapshot state.                                            | PM truth, chronicle, ConPort authority, bridge authority, source truth for retrieved files/docs.                  | `services/dope-context/src/mcp/server.py`, Docker `python -m src.mcp.server`, port `3010`.  |            HIGH | Completeness/freshness/ranking guarantees remain unknown.                   |
| `dopecon-bridge`           | Authenticated adapter/proxy routing, safe PM routing, ConPort proxy routes, event transport, health aggregation. | Canonical task/workflow/decision/progress/PM/chronicle/retrieval authority.                                       | `services/dopecon-bridge/main.py` + routes module.                                          |            HIGH | Operators may still mistake proxy routes as authority.                      |
| ADHD Engine                | Cognitive/operator-support state, recommendations, ADHD-focused APIs/MCP/events.                                 | PM truth, workflow legality, chronicle, ConPort authority, retrieval, CLI control.                                | `services/adhd_engine/main.py`, port `8095` internal / `3025` host.                         |          MEDIUM | Persistence backends for several surfaces unresolved.                       |
| Repo Truth Extractor       | Multi-phase extraction, doctor/preflight/status/coverage/proof artifacts.                                        | Runtime truth itself, PM, memory, retrieval, operator CLI authority.                                              | `services/repo-truth-extractor/run_extraction_v5.py`.                                       |            HIGH | Legacy `dopemux truth` path still drifts.                                   |
| Serena                     | Code-intelligence/MCP support surface.                                                                           | Canonical implementation/deployment authority until resolved.                                                     | UNKNOWN between service and Docker wrapper.                                                 |             LOW | Needs dedicated source pull.                                                |

**PM model:** split by concern. Metadata → Leantime; workflow transitions/views → task-orchestrator; decisions/progress/context → ConPort; historical receipts → dope-memory. 

**Memory model:** dope-memory is chronicle ledger authority; ConPort is structured context/decision/progress/custom-data authority where implemented; WMA is snapshot/recovery support, not proven as canonical chronicle. 

**Retrieval model:** dope-context owns derived code/docs retrieval and indexes; ConPort owns implemented structured/semantic context surfaces; retrieval output is never source truth. 

**Execution model:** operator command enters through `dopemux`, then hands off through `taskx` shim to `scripts/dopetask`, then external dopetask executes. 

**Data/event model:** durable state must be event-shaped or evidence-backed; required event envelope fields are `id`, `ts`, `workspace_id`, `instance_id`, `type`, `source`, and `data`; storage rules put declared SQLite as canonical and declared Postgres as mirror. 

---

## 5. Runtime authority map

| Domain                        | Canonical writer/store | Runtime authority                                                          | Status                     | Validation gate                                                           |
| ----------------------------- | ---------------------- | -------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------- |
| Operator CLI                  | `dopemux`              | `src/dopemux/cli.py`                                                       | OBSERVED by docs           | `python -m dopemux.cli --help` and console-script import check.           |
| Kernel execution              | external `dopetask`    | `scripts/dopetask`; `scripts/taskx` shim                                   | OBSERVED                   | `./scripts/dopetask --help`; `./scripts/taskx --help`; pin/version check. |
| PM metadata                   | Leantime               | adapters/JSON-RPC clients                                                  | OBSERVED by PM docs        | Exercise passive metadata update path with dry-run/stub.                  |
| PM workflow transitions       | task-orchestrator      | `app/main.py`, `project_workflow.py`, `pm_tools.py`                        | CONFLICTING packaging/port | Verify Docker target and exposed port before edits.                       |
| PM progress/decisions/context | ConPort                | CONFLICTING: Docker `enhanced_server.py` vs `src/conport/memory_server.py` | CONFLICTING                | Resolve deployed runtime, then freeze PM adapter URLs.                    |
| PM historical receipts        | dope-memory            | SQLite chronicle via `dope_memory_main.py`                                 | OBSERVED                   | Create/read chronicle entry against `.dopemux/chronicle.sqlite`.          |
| Chronicle storage             | SQLite                 | `ChronicleStore`, `canonical_ledger.py`                                    | OBSERVED                   | Ledger resolution fail-closed test.                                       |
| Postgres mirror               | Postgres               | dope-memory mirror worker                                                  | DERIVED                    | Prove mirror failure does not block SQLite success.                       |
| Code/docs retrieval           | dope-context           | Qdrant/BM25/snapshots via `src.mcp.server`                                 | DERIVED authority only     | Trace hit back to source file/doc.                                        |
| Bridge event/proxy            | dopecon-bridge         | FastAPI routes/event bus                                                   | TRANSPORT only             | Every bridge write must cite upstream canonical writer.                   |
| ADHD support state            | ADHD Engine            | `services/adhd_engine/main.py`                                             | PARTIAL                    | Identify persistence backends and fallback modes.                         |
| Repo truth extraction         | Repo Truth Extractor   | `run_extraction_v5.py`                                                     | OBSERVED                   | Run `--doctor`/status only when explicitly authorized.                    |

Task-orchestrator and ConPort are the two runtime-authority landmines. Task-orchestrator’s system doc says `app/main.py` is canonical, but Docker launches `task_orchestrator.app:app`, whose module hard-fails; ports also split between `8000` and `3014`.  ConPort’s system doc now favors Docker-packaged `enhanced_server.py`, while earlier truth scope elevated `src/conport/memory_server.py`; that contradiction must remain visible until runtime verification decides it. 

---

## 6. Documentation audit

| Doc                                |            Authority | Problems                                                        | Missing info                            | Needed fix                                                     | Priority | TP               |
| ---------------------------------- | -------------------: | --------------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------- | -------: | ---------------- |
| `01_RULES.md`                      |                 High | Strong, but broad.                                              | Concrete CI enforcement links.          | Add validation command appendix.                               |       P1 | DOC-GATE         |
| `02_PROJECT.md`                    |                 High | Accurate split model; still docs-derived.                       | Latest runtime verification.            | Add “last runtime verified” table.                             |       P1 | DOC-TRUST        |
| `03_ARCHITECTURE.md`               |                 High | Good multi-plane framing.                                       | Runtime proof timestamps.               | Add authority confidence ledger.                               |       P1 | DOC-TRUST        |
| `04_system-boundaries.md`          |                 High | Contains confusing task-orchestrator runtime wording.           | P0 runtime/port proof.                  | Replace ambiguous runtime authority with explicit CONFLICTING. |       P0 | TASKORCH-RUNTIME |
| `05_TRUTH_SCOPE.md`                |                 High | ConPort canonicality may conflict with system doc.              | Deployed runtime proof.                 | Refresh after ConPort audit.                                   |       P0 | CONPORT-AUTH     |
| `06_TRUTH_SYSTEMS.md`              |                 High | May preserve older runtime assumptions.                         | Live runtime recheck.                   | Regenerate from current extractor.                             |       P1 | SOURCE-PULL      |
| `07_TRUTH_INTERFACES.md`           |                 High | Interface truth includes known contradictions.                  | Current compose/registry validation.    | Add conflict matrix IDs.                                       |       P1 | RUNTIME-VERIFY   |
| `08_TRUTH_DATA_EVENTS.md`          |                 High | ADHD/dope-context persistence UNKNOWN.                          | Store writer traces.                    | Add storage-owner appendix.                                    |       P1 | STORAGE-AUDIT    |
| `09_TRUTH_CANONICALS.md`           |                 High | ConPort/task-orch drift unresolved.                             | Runtime proof.                          | Refresh canonical recommendations.                             |       P0 | CONPORT-AUTH     |
| `10_TRUTH_GAPS.md`                 |                 High | Good risk list, but static.                                     | Current gap status.                     | Convert into tracked backlog.                                  |       P1 | DOC-TRUST        |
| `11_SERVICE_CATALOG.md`            |          Medium-high | Tier 2 surfaces need runtime proof.                             | Serena, LiteLLM, webhook status.        | Add “verified/not verified” per tier.                          |       P2 | SOURCE-PULL      |
| `12_PM_PLANE.md`                   |                 High | Correct split; exposes port drift.                              | Unified PM read non-existence proof.    | Add PM validation runbook.                                     |       P0 | PM-PORTS         |
| `13_SYSTEM_Dopemux.md`             |                 High | Reports CLI import failure.                                     | Reproduction logs.                      | Add current CLI status and fix TP link.                        |       P0 | CLI-VERIFY       |
| `14_SYSTEM_Dopetask.md`            |                 High | External binary limits proof.                                   | Current pinned help output.             | Add fixture refresh command.                                   |       P1 | RUNTIME-VERIFY   |
| `15_SYSTEM_TaskOrchestrator.md`    |                 High | P0 Docker/module/port conflict.                                 | Actual container boot result.           | Reconcile or mark blocked.                                     |       P0 | TASKORCH-RUNTIME |
| `16_SYSTEM_ConPort.md`             | High but conflicting | Conflicts with older truth docs.                                | Active deployed runtime proof.          | Authority resolution doc patch.                                |       P0 | CONPORT-AUTH     |
| `17_SYSTEM_DopeMemory.md`          |                 High | Native MCP UNKNOWN; stale 8096 adapters.                        | Adapter inventory.                      | Add deprecation/runbook.                                       |       P1 | MEMORY-TRANSPORT |
| `18_SYSTEM_DopeContext.md`         |                 High | Wrapper/runtime mismatch known.                                 | Runtime smoke output.                   | Add wrapper reconciliation TP.                                 |       P1 | CONTEXT-WRAPPER  |
| `19_SYSTEM_DopeconBridge.md`       |                 High | Broad routes still dangerous.                                   | Route-to-writer map.                    | Add upstream writer matrix.                                    |       P0 | BRIDGE-WRITER    |
| `20_SYSTEM_ADHDEngine.md`          |               Medium | Persistence backends unresolved.                                | Store traces/fallback behavior.         | Add persistence section.                                       |       P1 | ADHD-STORAGE     |
| `21_SYSTEM_RepoTruthExtractor.md`  |                 High | Legacy command drift remains.                                   | Current operator entrypoint decision.   | Document canonical CLI path.                                   |       P1 | RTE-ENTRYPOINT   |
| `22_AGENTS.md`                     |          Medium-high | Agent authority UNKNOWN.                                        | Runtime owner decision.                 | Convert into explicit agent boundary policy.                   |       P1 | AGENTS-CREATE    |
| `23_PAL_EXECUTION_RULES.md`        |                 High | Good compressed doctrine.                                       | Tool availability mapping.              | Add project-specific chain mapping.                            |       P2 | PAL-ALIGN        |
| `24_PAL_CHAINING_DOCTRINE.md`      |                 High | Good but verbose.                                               | Project packet presets.                 | Link to packet recipes.                                        |       P2 | PAL-ALIGN        |
| `25_PAL_PACKET_TEMPLATE.md`        |               Medium | Human template may drift from JSON schema.                      | Schema equivalence check.               | Add warning: JSON schema wins.                                 |       P1 | TP-SCHEMA        |
| `26_dopetask-cannonical-spec.json` |     Highest contract | Filename typo “cannonical” is real, probably forever now.       | Schema examples.                        | Add valid sample packets.                                      |       P1 | TP-SCHEMA        |
| `27_REPO_STRUCTURE.md`             |            Generated | Can stale quickly.                                              | Manifest hash/timestamp.                | Regenerate only.                                               |       P3 | UPLOAD-REFRESH   |
| `28_SOURCE_AUTHORITY_MAP.md`       |            Generated | Advisory, not truth.                                            | Source provenance.                      | Regenerate from manifest.                                      |       P3 | UPLOAD-REFRESH   |
| `29_TOP40_SELECTION_RATIONALE.md`  |            Generated | Upload rationale not architecture.                              | Current file safety scan.               | Regenerate.                                                    |       P3 | UPLOAD-REFRESH   |
| `30_DRIFT_AND_GAPS_SUMMARY.md`     |            Generated | Mentions skipped secret-pattern docs.                           | Redacted review results.                | Add safe-pull plan.                                            |       P1 | SECRET-REDACT    |
| `31_RUNTIME_AUTHORITY_POINTERS.md` |            Generated | Pointers are not proof.                                         | Runtime verification outputs.           | Convert into executable check manifest.                        |       P0 | RUNTIME-VERIFY   |
| `32_CHATGPT_PROJECT_UPLOAD_SET.md` |            Generated | Useful but can stale.                                           | Current top-40 health.                  | Refresh after doc fixes.                                       |       P2 | UPLOAD-REFRESH   |
| `33_adapter-schema.md`             |             Contract | Needs schema test linkage.                                      | Adapter validator status.               | Add JSON schema tests.                                         |       P2 | ADAPTER-VALIDATE |
| `34_adapter-contract.md`           |             Contract | Good invariants, needs implementation proof.                    | Adapter code status.                    | Link to tests/proof bundle.                                    |       P2 | ADAPTER-VALIDATE |
| `35_proof-bundle-schema.md`        |             Contract | Good schema prose.                                              | Machine schema absent.                  | Add JSON schema.                                               |       P1 | PROOF-SCHEMA     |
| `36_proof-contract.md`             |             Contract | Strong minimums.                                                | Enforcer status.                        | Add proof gate script.                                         |       P1 | PROOF-GATE       |
| `37_handoff-contract.md`           |             Contract | Strong minimums.                                                | Enforcer status.                        | Add handoff validator.                                         |       P1 | HANDOFF-GATE     |
| `38_TEMPLATE_TASK_PACKET.md`       |             Template | Does not equal strict JSON schema.                              | Crosswalk.                              | Add “legacy/human-readable” label.                             |       P1 | TP-SCHEMA        |
| `39_INDEX.md`                      |   Registry/generated | Could be stale; active packet list must not be blindly trusted. | Runtime packet registry check.          | Add index validation gate.                                     |       P1 | TP-INDEX         |
| `40_agents.instructions.md`        |   Agent instructions | Needs current GitHub docs alignment.                            | Copilot feature support by environment. | Create `.github/agents` from this with tests.                  |       P1 | AGENTS-CREATE    |

---

## 7. Missing information matrix

| Gap                                    | Why                                                           | Source                                       | Retrieval method                    | Tool           |      Blocking | TP               |
| -------------------------------------- | ------------------------------------------------------------- | -------------------------------------------- | ----------------------------------- | -------------- | ------------: | ---------------- |
| Live runtime code/config not uploaded  | Runtime outranks docs.                                        | Bundle only contains docs/contracts.         | Source pull / repo checkout.        | shell/Codex    |           Yes | RUNTIME-VERIFY   |
| Task-orchestrator container boot truth | Docker target and active code conflict.                       | `15_SYSTEM_TaskOrchestrator.md`.             | Compose boot + HTTP smoke.          | Codex/shell    |           Yes | TASKORCH-RUNTIME |
| ConPort deployed authority             | Docker runtime and `src/conport` conflict.                    | `05_TRUTH_SCOPE.md`, `16_SYSTEM_ConPort.md`. | Compose/registry/build inspection.  | Gemini + Codex |           Yes | CONPORT-AUTH     |
| PM adapter endpoint truth              | `3004`, `3005`, `3014`, `8000` drift.                         | `12_PM_PLANE.md`.                            | Static grep + integration smoke.    | Codex          |           Yes | PM-PORTS         |
| dope-memory native MCP support         | Active HTTP tools proven; native MCP not proven.              | `17_SYSTEM_DopeMemory.md`.                   | Route inspection + smoke.           | Codex          | No, but risky | MEMORY-TRANSPORT |
| WMA persistent writers                 | Snapshot/recovery store unresolved.                           | truth/system docs.                           | Trace write paths.                  | Codex          |        Medium | WMA-STORAGE      |
| ADHD persistence backends              | Runtime state and fallback exist; exact stores partial.       | `20_SYSTEM_ADHDEngine.md`.                   | Trace store/client paths.           | Codex          |        Medium | ADHD-STORAGE     |
| Serena canonical runtime               | Docker wrapper vs in-repo implementation unresolved.          | `10_TRUTH_GAPS.md`, service catalog.         | Dedicated source pull.              | Gemini         |        Medium | SERENA-AUTH      |
| Agent authority                        | Three families; no canonical runtime.                         | `22_AGENTS.md`.                              | Runtime/compose/search audit.       | Gemini         |        Medium | AGENTS-AUTH      |
| Secret-skipped docs                    | 34 skipped files may contain useful docs but unsafe patterns. | `30_DRIFT_AND_GAPS_SUMMARY.md`.              | Redacted pull, fail-closed scanner. | shell/Codex    |        Medium | SECRET-REDACT    |
| Proof/handoff validator status         | Contracts exist, enforcers unknown.                           | `35-37`.                                     | Search tests/CI.                    | Codex          |        Medium | PROOF-GATE       |
| ChatGPT upload freshness               | Top-40 generated set may stale.                               | `32_CHATGPT_PROJECT_UPLOAD_SET.md`.          | Regenerate manifest.                | shell          |           Low | UPLOAD-REFRESH   |

---

## 8. Documentation backlog

| Rank | Doc                                                         | Exact fix                                                          | Evidence needed                                 | Agent          | Validation                                         | Risk                               | TP               |
| ---: | ----------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------- | -------------- | -------------------------------------------------- | ---------------------------------- | ---------------- |
|    1 | `15_SYSTEM_TaskOrchestrator.md` + `04_system-boundaries.md` | Replace conflicting runtime claims with verified launch path/port. | Compose boot, Dockerfile, health check.         | Codex          | Container starts and `/health` returns.            | P0 wrong workflow authority.       | TASKORCH-RUNTIME |
|    2 | `16_SYSTEM_ConPort.md` + `05/09_TRUTH_*.md`                 | Resolve Docker vs `src/conport` authority without erasing history. | Compose/registry/build path.                    | Gemini + Codex | One canonical runtime row plus archived alternate. | P0 wrong structured truth surface. | CONPORT-AUTH     |
|    3 | `12_PM_PLANE.md`                                            | Add PM endpoint validation runbook and port map.                   | Adapter defaults + compose/registry.            | Codex          | Static grep + smoke tests.                         | P0 PM writes hit wrong service.    | PM-PORTS         |
|    4 | `31_RUNTIME_AUTHORITY_POINTERS.md`                          | Convert pointer doc into executable manifest.                      | Runtime authority table.                        | Codex          | Script exits nonzero on drift.                     | P0 false confidence.               | RUNTIME-VERIFY   |
|    5 | `19_SYSTEM_DopeconBridge.md`                                | Add route-to-upstream-writer matrix.                               | Bridge routes and clients.                      | Codex          | Every write route names upstream writer.           | P0 bridge authority inflation.     | BRIDGE-WRITER    |
|    6 | `17_SYSTEM_DopeMemory.md`                                   | Add transport deprecation section for `8096` adapter.              | Adapter route/port audit.                       | Codex          | Stale adapter flagged or fixed.                    | P1 memory writes vanish.           | MEMORY-TRANSPORT |
|    7 | `13_SYSTEM_Dopemux.md`                                      | Reproduce/fix CLI import failure or mark obsolete.                 | `python -m dopemux.cli --help`.                 | Codex          | Import and CLI help pass.                          | P1 operator surface broken.        | CLI-VERIFY       |
|    8 | `25/38 TP templates`                                        | Crosswalk human template to strict JSON schema.                    | JSON schema validation.                         | Codex          | Valid sample packets pass schema.                  | P1 invalid packets.                | TP-SCHEMA        |
|    9 | `22_AGENTS.md` + `40_agents.instructions.md`                | Create actual agent files and boundaries.                          | Current Copilot/Claude docs + repo constraints. | Codex          | Agent lint + dry-run review.                       | P1 agent sprawl.                   | AGENTS-CREATE    |
|   10 | `32_CHATGPT_PROJECT_UPLOAD_SET.md`                          | Refresh upload strategy after doc fixes.                           | Manifest/hash scan.                             | shell          | Top-40 regenerated, unsafe files excluded.         | P2 stale project context.          | UPLOAD-REFRESH   |

---

## 9. Doc promotion/demotion decisions

| Decision                      | Docs                                                                               | Why                                                                    | Implementation path                          | Validation                                | Risk                            |
| ----------------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------------- | ------------------------------- |
| Promote                       | `01_RULES.md`, `02_PROJECT.md`, `03_ARCHITECTURE.md`, `12_PM_PLANE.md`             | These define repo truth discipline and current operating model.        | Make them first-batch ChatGPT Project files. | Cross-check against latest `TRUTH_*`.     | Low if refreshed.               |
| Promote after repair          | `04_system-boundaries.md`, `15_SYSTEM_TaskOrchestrator.md`, `16_SYSTEM_ConPort.md` | They are essential but contain unresolved runtime contradictions.      | Run P0 authority TPs, then patch.            | Runtime smoke + docs diff.                | High if promoted before repair. |
| Promote                       | `17-19_SYSTEM_*`, `21_SYSTEM_RepoTruthExtractor.md`                                | Boundaries are strong and authority slices narrow.                     | Keep in system batch.                        | Search for overclaim terms.               | Medium.                         |
| Promote with caveats          | `20_SYSTEM_ADHDEngine.md`, `11_SERVICE_CATALOG.md`                                 | Useful but persistence/Tier 2 status unresolved.                       | Add `UNKNOWN` rows.                          | Store/path trace.                         | Medium.                         |
| Keep local/generated          | `27-32`                                                                            | Navigation and upload docs are derived.                                | Regenerate from manifest.                    | Hash/timestamp match.                     | Medium if treated as truth.     |
| Keep but subordinate          | `33-38`                                                                            | Contracts/templates are useful but must not outrank schema/runtime.    | Add schema validators.                       | JSON schema and proof/handoff validation. | Medium.                         |
| Keep as registry only         | `39_INDEX.md`                                                                      | Useful traceability registry, but may stale.                           | Validate packet statuses from repo.          | Index consistency check.                  | Medium.                         |
| Promote as agent policy       | `22_AGENTS.md`, `40_agents.instructions.md`                                        | Needed for AI workflow, but not architecture truth.                    | Build concrete agent specs.                  | Agent-file lint and workflow dry run.     | Medium.                         |
| Do not upload raw unsafe docs | Secret-skipped files from drift summary                                            | Secret patterns found. Humanity invented docs with secrets, naturally. | Redact first, fail closed.                   | Secret scanner twice.                     | High.                           |
| Do not delete yet             | Duplicate/stale docs                                                               | Need provenance before removal.                                        | Demote/archive only after doc trust map.     | Link checker + search references.         | Medium.                         |

---

## 10. Development methodology

**Truth hierarchy:** runtime code/config/compose/tests outrank truth artifacts; `TRUTH_*.md` outrank canonical docs; canonical docs outrank system docs; generated docs are advisory. 

**Workflow invariant:** every non-trivial repo-changing task must have a strict Task Packet, a fresh dedicated worktree, repo identity verification, branch verification, commit-sized slices, codereview, precommit, pushed branch, opened PR, proof ledger, and cleanup status. 

**Execution discipline:** Codex minimum chain is `analyze -> planner -> codereview -> precommit`; default PAL chain is `analyze -> thinkdeep -> challenge -> planner -> challenge -> codereview -> precommit -> challenge`; final confidence must be `VERIFIED`. 

**State/data discipline:** all durable state must be event-shaped or evidence-backed; promotion is limited to decisions, task outcomes, errors, and workflow transitions; redaction happens before storage and again before promotion; idempotency uses `event_id`. 

**Retrieval discipline:** Phase 1 retrieval is keyword-only and deterministic; no semantic magic or LLM scoring; retrieval output is derived evidence, not source truth. 

---

## 11. PAL / TP doctrine

| Doctrine item                   | Rule                                                                                                         | Dopemux application                                                              |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Validated understanding first   | No planner before `MEDIUM` confidence.                                                                       | Runtime authority TPs start with static/runtime inspection.                      |
| Challenge before implementation | Plans must be pressure-tested.                                                                               | P0 authority repairs require challenge before edits.                             |
| Debug only for concrete failure | Debug is not incense.                                                                                        | Use debug for CLI import failure, container boot failure, port mismatch.         |
| Codereview before precommit     | Precommit is final gate, not first review.                                                                   | Every implementation TP includes review before final validation.                 |
| Stage artifacts                 | Each stage includes summary, evidence ledger, assumptions, confidence, next action.                          | Proof bundles and handoffs consume these.                                        |
| Commit-sized slices             | Validate after each meaningful slice.                                                                        | One slice per runtime conflict or doc cluster.                                   |
| TP schema                       | Required top-level fields: `id`, `project`, `target`, `repo_binding`, `series`, `commit`, `pr`, `steps`.     | All packets below use only schema-declared fields.                               |
| Gemini rule                     | If `execution.agent = "gemini"`, `pal_chain.enabled = true` is required.                                     | Gemini audit packets include full PAL chain.                                     |
| Proof                           | Substantive runs emit primary report, manifest, blockers/warnings if present, handoff when needed.           | PR handoff cannot be “trust me bro.”                                             |
| Handoff                         | Handoff includes source/target skill, repo/branch, posture, artifacts, warnings, blockers, chain of custody. | Required when control moves between ChatGPT, Codex, Claude, Gemini, or Copilot.  |

The strict JSON schema declares no undeclared top-level fields and has `additionalProperties: false`; step objects require `id`, `task`, and `validation`; Gemini packets must include `pal_chain` with `enabled: true`. 

---

## 12. Drift matrix

| ID    | Area                      | Claim A                                                                           | Claim B                                                                  | Evidence                                            | Risk                                       | Resolution                                        |
| ----- | ------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------- | ------------------------------------------ | ------------------------------------------------- |
| D-001 | Task-orchestrator runtime | `app/main.py` is active runtime.                                                  | Docker launches `task_orchestrator.app:app`, which hard-fails.           | `15_SYSTEM_TaskOrchestrator.md`.                    | Container cannot boot or docs lie.         | Do not resolve narratively; run TASKORCH-RUNTIME. |
| D-002 | Task-orchestrator port    | Compose/registry/Docker use `8000`.                                               | App/defaults and adapters use `3014`.                                    | `15_SYSTEM_TaskOrchestrator.md`, `12_PM_PLANE.md`.  | PM writes/read clients hit wrong port.     | Verify and standardize.                           |
| D-003 | ConPort runtime           | `src/conport/memory_server.py` active in truth scope.                             | Docker `enhanced_server.py` primary in system doc.                       | `05_TRUTH_SCOPE.md`, `16_SYSTEM_ConPort.md`.        | Wrong structured truth runtime.            | Runtime authority audit.                          |
| D-004 | ConPort ports/tools       | HTTP `3004`, SSE `3005`, info `4004`.                                             | PM reads split `3004`/`3005`; tools differ by transport.                 | ConPort/PM docs.                                    | Inconsistent PM context/decision behavior. | Freeze PM ConPort contract.                       |
| D-005 | dope-memory transport     | Active HTTP runtime `3020`.                                                       | Legacy WMA/default adapter `8096`.                                       | `17_SYSTEM_DopeMemory.md`.                          | Memory calls disappear into stale port.    | Deprecate/fix adapters.                           |
| D-006 | dope-memory MCP           | HTTP `/tools/*` proven.                                                           | Native `/mcp` not proven.                                                | `17_SYSTEM_DopeMemory.md`.                          | Tools misconfigured in MCP clients.        | Mark UNKNOWN or implement wrapper.                |
| D-007 | dope-context runtime      | Docker `/info` says `python -m src.mcp.server`.                                   | Wrapper executes `/app/server.py`; legacy `run_mcp.sh` references exist. | `18_SYSTEM_DopeContext.md`.                         | Retrieval service launch failure.          | Reconcile wrapper/config.                         |
| D-008 | Bridge authority          | Bridge exposes `/kg/*`, `/ddg/*`, `/route/pm`.                                    | Bridge must not own task/workflow/decision/progress authority.           | Boundary and bridge docs.                           | Silent authority inflation.                | Add route-to-writer matrix.                       |
| D-009 | Agent runtime             | `services/agents`, `src/dopemux/agent_orchestrator.py`, task-orchestrator agents. | No single agent authority proven.                                        | `22_AGENTS.md`.                                     | Agents mutate wrong plane.                 | Agent authority audit.                            |
| D-010 | Repo truth extraction     | `run_extraction_v5.py` strongest runtime.                                         | Legacy `dopemux truth` / PipelineRunner still exists.                    | Repo Truth Extractor docs.                          | Operators run stale extractor.             | Canonical CLI decision.                           |
| D-011 | Generated docs            | Top-40 upload set useful.                                                         | Generated docs can stale and are advisory.                               | upload/source docs.                                 | ChatGPT context decays into fiction.       | Regenerate after P0 repairs.                      |
| D-012 | Secret-skipped docs       | Some skipped docs may contain runbooks.                                           | Unsafe patterns prevent direct upload.                                   | drift summary.                                      | Missing info or secret leakage.            | Redacted source pull.                             |

---

## 13. AI tool role matrix

Current tool design should use each AI tool for a bounded role, not as a democracy of stochastic raccoons. OpenAI’s current ChatGPT Projects support uploaded reference materials, and Codex is documented as a coding agent/worktree-oriented environment; GitHub documents Copilot custom agents as Markdown/YAML profiles with tools/MCP configuration; Anthropic documents Claude Code subagents; Google documents Gemini MCP/skills and agent tooling for current Gemini development. ([OpenAI Help Center][1])

| Tool                         | Best use                                                                                  | Forbidden use                                                           | Inputs                                                       | Outputs                                                | Guardrails                                                                                                                                 |
| ---------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| ChatGPT / GPT-5.5 Pro        | Supervisor, truth extraction, TP generation, doc repair planning, cross-source synthesis. | Direct repo mutation, claiming runtime verification without evidence.   | Uploaded top authority docs, runtime outputs, proof bundles. | TPs, review matrices, prompt library, operating model. | Must preserve `UNKNOWN`, cite sources, max Top-3 for operator lists unless deep audit requested.                                           |
| Codex                        | Commit-sized implementation in dedicated worktrees; code/doc edits; tests; diffs.         | Architecture invention, broad unsliced refactors, hidden cleanup.       | Approved TP, repo checkout, branch/worktree.                 | Diff, tests, proof ledger, PR.                         | `analyze -> planner -> codereview -> precommit`; no work outside allowlist.                                                                |
| Claude                       | Adversarial review, doc clarity review, reasoning critique.                               | Canonical writer decisions without runtime proof.                       | Diff, TP, docs, evidence ledger.                             | Review findings, severity list, suggested fixes.       | Must separate style issues from architecture violations.                                                                                   |
| Claude Code                  | Interactive local exploration, subagent-assisted review, tactical refactor support.       | Acting as PM/memory/retrieval authority.                                | Worktree, scoped prompt, file allowlist.                     | Local edits or reviews.                                | Use custom subagents with clear descriptions and tool limits. ([Claude API Docs][2])                                                       |
| GitHub Copilot custom agents | Repo-level modular roles: planner, implementer, reviewer, testgen.                        | Large orchestration, bulk source processing, authority decisions.       | `.github/agents/*.agent.md`, TP, branch context.             | Guided IDE/cloud-agent outputs.                        | Minimal tools, explicit handoffs, 2-3 next steps max, current environment support checked. ([GitHub Docs][3])                              |
| Gemini                       | Cross-audit, long-context contradiction search, external API/source review.               | Implementation without PAL chain; final truth claims from search alone. | Full doc bundle, runtime artifacts, source maps.             | Audit report, conflict matrix, missing-info list.      | `execution.agent="gemini"` requires `pal_chain.enabled=true`; use MCP/current docs for API-sensitive work. ([Google AI for Developers][4]) |

---

## 14. Multi-agent workflow

| Step | Action          | Owner          | Gate                                            | Output                       |
| ---: | --------------- | -------------- | ----------------------------------------------- | ---------------------------- |
|    1 | Source intake   | ChatGPT        | Source authority map loaded                     | Classified sources           |
|    2 | Scope           | ChatGPT        | Authority boundaries named                      | TP target + allowlist        |
|    3 | TP creation     | ChatGPT        | JSON schema conformity                          | Strict TP                    |
|    4 | Worktree        | Codex/shell    | Fresh dedicated worktree from base branch       | Worktree path                |
|    5 | Verify repo     | Codex/shell    | Marker + origin + branch + not primary checkout | Verification report          |
|    6 | Implement slice | Codex          | Allowlist only                                  | Diff slice                   |
|    7 | Validate        | Codex          | Smallest relevant commands pass                 | Test logs                    |
|    8 | Diff inspect    | Codex + Claude | No out-of-scope changes                         | Review notes                 |
|    9 | Codereview      | Claude/Codex   | Findings triaged                                | Review artifact              |
|   10 | Precommit       | Codex          | Final checks pass                               | Precommit report             |
|   11 | Proof bundle    | Codex          | Manifest + warnings/blockers + chain of custody | Proof bundle                 |
|   12 | PR              | Codex/shell    | Branch pushed, PR opened                        | PR URL                       |
|   13 | Handoff         | ChatGPT        | Proof ingested, residual risks explicit         | Next TP or completion report |

Every workflow transition should emit an event envelope with `id`, `ts`, `workspace_id`, `instance_id`, `type`, `source`, and `data`; retries must be idempotent via `event_id`. 

---

## 15. ChatGPT usage model

Use ChatGPT Projects as the **supervisor workspace**, not the implementation engine. OpenAI’s Projects documentation says projects can hold chats, files, and instructions under a shared objective, and can use uploaded reference materials to answer with project context. ([OpenAI Help Center][1])

**Project structure:**

| Project folder / upload group | Contents                                                                          | Use                       |
| ----------------------------- | --------------------------------------------------------------------------------- | ------------------------- |
| Batch 1                       | `RULES`, `PROJECT`, `ARCHITECTURE`, `SYSTEM_BOUNDARIES`, `TRUTH_*`                | Authority and truth base  |
| Batch 2                       | `SERVICE_CATALOG`, `PM_PLANE`, primary `SYSTEM_*`                                 | System boundary reasoning |
| Batch 3                       | Repo Truth Extractor, AGENTS, PAL, schema, generated maps                         | Execution doctrine        |
| Batch 4                       | runtime pointers, upload set, adapter/proof/handoff contracts, agent instructions | Implementation guardrails |

**Retrieval rule:** ChatGPT may summarize and synthesize uploaded docs, but it must not convert retrieval hits into source truth. For runtime claims, require logs, command output, or code excerpts from the actual repo. The uploaded project set already separates authoritative, derived, advisory, and generated materials; keep that hierarchy visible.

---

## 16. Codex model

Codex should be the **implementation executor**. OpenAI’s current Codex app documentation describes a desktop experience for parallel Codex threads with worktree support, automations, and Git functionality, which maps neatly onto Dopemux’s mandatory fresh-worktree discipline. ([OpenAI Developers][5])

| Codex phase | Required behavior                                                   |
| ----------- | ------------------------------------------------------------------- |
| Intake      | Read TP, refuse if schema invalid or allowlist missing.             |
| Analyze     | Identify exact files, entrypoints, tests, drift.                    |
| Plan        | Produce slice plan and validation per slice.                        |
| Implement   | Touch only allowlisted files.                                       |
| Validate    | Run exact commands in TP.                                           |
| Codereview  | Inspect diff and architecture boundaries.                           |
| Precommit   | Final gate, no unresolved P0/P1 findings.                           |
| Proof       | Produce diff stat, command output, risks, worktree/branch/PR proof. |

Codex must not silently “improve” nearby docs, rename unrelated services, or beautify reality. That way lies startup architecture decks and other ornamental crimes.

---

## 17. Claude Code model

Claude Code should be used for **interactive local reasoning and review**, especially when its subagent system can divide work into exploration, planning, review, and documentation. Anthropic documents Claude Code custom subagents with descriptions that guide delegation, which is useful for bounded review roles. ([Claude API Docs][2])

| Claude Code role  | Scope                                                 |
| ----------------- | ----------------------------------------------------- |
| Explore subagent  | Read-only scan of a subsystem and safe edit points.   |
| Plan subagent     | Produce alternative plans only after evidence intake. |
| Reviewer subagent | Review diff against architecture invariants.          |
| Docs subagent     | Update docs after code stabilizes.                    |
| Security subagent | Review auth/secrets/network-facing changes.           |

Forbidden: Claude Code must not be allowed to decide canonical PM/memory/retrieval authority from prose alone. It can critique evidence; it cannot crown a bridge king because the route names looked important. 👑

---

## 18. Copilot agent model

GitHub Copilot custom agents should live under `.github/agents/` as narrow repo-level agents. GitHub’s current docs describe custom agent profiles as Markdown files with YAML frontmatter specifying name, description, tools, and MCP configuration; the uploaded `40_agents.instructions.md` also requires concise descriptions, tool limits, model selection, target, and handoff discipline. ([GitHub Docs][6]) 

| Agent file                                    | Purpose                                  | Tools                               | Handoff            |
| --------------------------------------------- | ---------------------------------------- | ----------------------------------- | ------------------ |
| `.github/agents/dopemux-planner.agent.md`     | Plan from TP and repo evidence.          | `read`, `search`                    | Implement          |
| `.github/agents/dopemux-implementer.agent.md` | Execute allowlisted slice.               | `read`, `edit`, `search`, `execute` | Review             |
| `.github/agents/dopemux-reviewer.agent.md`    | Review boundary, tests, security, drift. | `read`, `search`                    | Testgen or planner |
| `.github/agents/dopemux-testgen.agent.md`     | Add/repair tests only.                   | `read`, `edit`, `search`, `execute` | Review             |

**Agent guardrails:** no agent may alter `target`, `repo_binding`, `series`, or `steps` in an approved TP. The orchestrator’s tool permissions cap sub-agent permissions, so don’t give the planner `edit` unless you enjoy avoidable messes. 

---

## 19. Gemini audit model

Gemini should be used as the **cross-audit agent**, not the default implementer. Google’s current Gemini developer docs emphasize MCP/skills for coding assistants and current API-aware workflows; that makes Gemini a good source-pull and contradiction-audit tool when paired with Dopemux’s mandatory PAL chain. ([Google AI for Developers][4])

| Gemini audit phase     | Output                                 |
| ---------------------- | -------------------------------------- |
| Source intake          | Conflicting claims by file and path.   |
| Runtime pointer audit  | Which claims need live repo proof.     |
| Drift classification   | P0/P1/P2/P3 with source citations.     |
| Missing-info retrieval | Exact files/commands needed.           |
| PAL challenge          | Whether plan is safe to hand to Codex. |

If a TP sets `execution.agent` to `gemini`, the packet must include `pal_chain.enabled=true`; the project schema enforces this, because apparently even JSON has to save us from vibes. 

---

## 20. Prompt library

### Supervisor prompt

```text
You are the Dopemux supervisor. Use source authority order strictly:
runtime > TRUTH_* > canonical docs > SYSTEM_* > contracts > generated docs.
Classify each claim as OBSERVED, INFERRED, RECOMMENDED, UNKNOWN, or CONFLICTING.
Do not merge planes. Do not treat bridge/proxy/retrieval/mirror output as source truth.
Return: items, more_count, next_token for state lists; for non-trivial work, emit a strict TP.
```

### TP generator prompt

```text
Generate a dopetask-cannonical-spec.json-conformant Task Packet.
Use only declared schema fields.
Every step must include id, task, validation.
Set repo_binding.repo_marker=".dopetaskroot".
Add execution.agent.
If execution.agent="gemini", include pal_chain.enabled=true.
No implementation work may happen before fresh worktree and repo identity verification.
```

### Codex implementer prompt

```text
Execute only the approved TP.
Before edits: verify repo marker, origin, branch, worktree path, and that this is not the primary checkout.
Touch only commit.allowlist.
After each slice: run validation, inspect diff, report evidence.
Stop on mismatch, unexpected runtime behavior, secret exposure, or authority ambiguity.
```

### Claude reviewer prompt

```text
Review this diff against Dopemux boundaries.
Classify findings as P0/P1/P2/P3.
Check for: authority inflation, bridge-as-truth, retrieval-as-truth, mirror-as-truth,
cross-plane mutation, missing tests, secret leakage, and doc/runtime drift.
Return required fixes only; style nits go last.
```

### Gemini auditor prompt

```text
Audit the supplied Dopemux bundle for contradictions.
Do not resolve conflicts unless runtime evidence proves resolution.
Produce: source map, drift matrix, missing-info matrix, P0/P1 blockers, and exact next TPs.
If evidence is missing, mark UNKNOWN and name the source pull required.
```

### Copilot planner agent prompt body

```text
You are Dopemux Planner.
Read the TP and repo docs. Do not edit files.
Produce a commit-sized implementation plan with safe edit points, validations, assumptions, and stop conditions.
Do not invent runtime authority.
```

### Copilot implementer agent prompt body

```text
You are Dopemux Implementer.
Implement the approved plan exactly.
Use only allowed files and commands.
Return diff stat, validation outputs, exit codes, and residual risks.
```

### Copilot reviewer agent prompt body

```text
You are Dopemux Reviewer.
Review the diff for correctness, architecture boundaries, security, test coverage, and proof completeness.
Do not rewrite the implementation unless explicitly handed off.
```

### Copilot testgen agent prompt body

```text
You are Dopemux Testgen.
Add or repair tests only for the scoped behavior.
Do not edit production code unless the TP explicitly allows it.
Return test files changed, commands run, and coverage gaps.
```

---

## 21. Top 10 improvements

| Rank | Improvement                                   | Why                                       | Evidence                               | Implementation path                              | Validation                         | Risk |
| ---: | --------------------------------------------- | ----------------------------------------- | -------------------------------------- | ------------------------------------------------ | ---------------------------------- | ---- |
|    1 | Executable runtime authority verifier         | Pointer docs are not proof.               | `31_RUNTIME_AUTHORITY_POINTERS.md`.    | Add script/config to validate entrypoints/ports. | Script fails on known drift.       | P0   |
|    2 | Task-orchestrator runtime/port reconciliation | Docker and app disagree.                  | `15_SYSTEM_TaskOrchestrator.md`.       | Fix Docker/import/ports or docs.                 | Compose + `/health`.               | P0   |
|    3 | ConPort authority resolution                  | Runtime surfaces conflict.                | `16_SYSTEM_ConPort.md` vs truth scope. | Audit deployed path; patch docs/config.          | One canonical runtime result.      | P0   |
|    4 | Bridge route-to-writer matrix                 | Bridge routes look authoritative.         | `19_SYSTEM_DopeconBridge.md`.          | Add route table naming upstream writer.          | Every write route has writer.      | P0   |
|    5 | PM adapter port contract                      | PM uses split endpoints.                  | `12_PM_PLANE.md`.                      | Centralize/validate defaults.                    | Static grep + smoke.               | P0   |
|    6 | Memory transport cleanup                      | `3020` active, `8096` stale.              | `17_SYSTEM_DopeMemory.md`.             | Deprecate/fix stale adapters.                    | Adapter smoke.                     | P1   |
|    7 | CLI import verification/fix                   | Dopemux CLI reportedly broken.            | `13_SYSTEM_Dopemux.md`.                | Reproduce and fix import.                        | CLI help passes.                   | P1   |
|    8 | Strict TP examples/validator                  | Schema exists but examples/gates missing. | `26` + templates.                      | Add sample packets + validator command.          | JSON schema passes/fails fixtures. | P1   |
|    9 | Agent file creation                           | Agent authority is undefined.             | `22`, `40`.                            | Add `.github/agents` role files.                 | Agent lint + dry-run.              | P1   |
|   10 | Upload set regeneration                       | Generated docs stale.                     | `32`.                                  | Regenerate after P0 fixes.                       | Manifest + hash comparison.        | P2   |

---

## 22. Top 10 doc/gap fixes

| Rank | Fix                                     | Why                                  | Evidence                    | Implementation path             | Validation                       | Risk |
| ---: | --------------------------------------- | ------------------------------------ | --------------------------- | ------------------------------- | -------------------------------- | ---- |
|    1 | Create `DOC_TRUST_MAP.md`               | Operators need trust levels.         | Docs audit prompt history.  | Audit all docs against runtime. | Every doc has trust level.       | P0   |
|    2 | Create `DOCS_VS_REPO_DIFF.md`           | Drift must be visible.               | Same audit packet.          | Static/runtime comparison.      | Mismatches classified.           | P0   |
|    3 | Patch `SYSTEM_BOUNDARIES` task-orch row | Current wording can mislead.         | Boundary/system docs.       | Mark CONFLICTING.               | No false authority row.          | P0   |
|    4 | Patch ConPort docs after audit          | Avoid wrong structured truth target. | ConPort conflict.           | Authority resolution.           | Runtime proof included.          | P0   |
|    5 | Patch PM plane port map                 | PM clients risk wrong port.          | PM drift list.              | Add canonical endpoints table.  | Grep/default consistency.        | P0   |
|    6 | Add bridge upstream writer appendix     | Prevent bridge authority inflation.  | Bridge docs.                | Route-to-writer map.            | No write route without upstream. | P0   |
|    7 | Add memory transport runbook            | Fix `3020`/`8096` confusion.         | Dope-memory docs.           | Active/legacy transport table.  | Adapter tests.                   | P1   |
|    8 | Add proof/handoff validators            | Contracts need enforcement.          | Proof/handoff docs.         | JSON schemas + CLI validation.  | Fixtures pass.                   | P1   |
|    9 | Redacted unsafe-doc retrieval plan      | Skipped docs may hold runbooks.      | Drift summary.              | Secret scanner + redaction.     | Two-pass scan.                   | P1   |
|   10 | Agent authority decision record         | Agent sprawl needs boundaries.       | `AGENTS.md`.                | Create ADR or system doc.       | No agent owns PM/memory truth.   | P1   |

---

## 23. Top 3 implementation TPs

The packets below use only schema-declared fields from `26_dopetask-cannonical-spec.json`; they are plan packets, not proof of completed work. PR URLs appear only after execution, because time travel remains disappointingly unavailable.

### TP 1 — Runtime authority verifier

```json
{
  "id": "TP-DMX-RUNTIME-VERIFY-001",
  "project": "dopemux",
  "target": "RUNTIME_VERIFY: add deterministic runtime authority verifier for canonical entrypoints, ports, and wrappers",
  "invariants": [
    "Runtime code/config/tests outrank generated docs",
    "Verifier must not mutate production state",
    "Bridge/proxy/retrieval/mirror surfaces must not be promoted to authority"
  ],
  "depends_on": [],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "audit/runtime-authority-verifier"
  },
  "commit": {
    "message": "Add deterministic runtime authority verifier",
    "allowlist": [
      "scripts/verify_runtime_authority.py",
      "config/runtime_authority_manifest.json",
      "tests/unit/test_runtime_authority_manifest.py",
      "docs/03-reference/runtime-authority-verification.md"
    ],
    "verify": [
      "python -m json.tool config/runtime_authority_manifest.json",
      "python -m pytest -q tests/unit/test_runtime_authority_manifest.py",
      "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
    ]
  },
  "pr": {
    "title": "Add deterministic runtime authority verifier",
    "body": "Adds a static/runtime authority verification harness for Dopemux entrypoints, ports, wrappers, and canonical writer boundaries.",
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
      "task": "Create a manifest that lists expected canonical runtime pointers for dopemux, dopetask, task-orchestrator, ConPort, dope-memory, dope-context, dopecon-bridge, ADHD Engine, and Repo Truth Extractor.",
      "requirements": [
        "Mark known conflicts as expected_conflict instead of resolving them",
        "Do not assert runtime truth for UNKNOWN surfaces"
      ],
      "commands": [
        "python -m json.tool config/runtime_authority_manifest.json"
      ],
      "expected_files": [
        "config/runtime_authority_manifest.json"
      ],
      "validation": [
        "Manifest parses as JSON",
        "Every entry has system, expected_paths, authority_status, and validation_mode"
      ],
      "context_files": [
        "01_RULES.md",
        "31_RUNTIME_AUTHORITY_POINTERS.md",
        "10_TRUTH_GAPS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Implement a verifier script that performs deterministic static checks for required files, forbidden legacy targets, known port conflicts, and wrapper target mismatches.",
      "requirements": [
        "No network calls in static mode",
        "Stable ordering of reported findings",
        "Exit nonzero on unexpected missing authority files"
      ],
      "commands": [
        "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
      ],
      "expected_files": [
        "scripts/verify_runtime_authority.py"
      ],
      "validation": [
        "Static verifier reports known conflicts deterministically",
        "Unexpected missing files produce nonzero exit"
      ],
      "context_files": [
        "04_system-boundaries.md",
        "15_SYSTEM_TaskOrchestrator.md",
        "16_SYSTEM_ConPort.md"
      ]
    },
    {
      "id": "S3",
      "task": "Add unit tests and verification documentation for the authority verifier.",
      "requirements": [
        "Tests must not require Docker",
        "Docs must warn that the verifier supports runtime truth but does not replace runtime execution"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_runtime_authority_manifest.py"
      ],
      "expected_files": [
        "tests/unit/test_runtime_authority_manifest.py",
        "docs/03-reference/runtime-authority-verification.md"
      ],
      "validation": [
        "Unit tests pass",
        "Docs include failure handling and proof expectations"
      ],
      "context_files": [
        "23_PAL_EXECUTION_RULES.md",
        "36_proof-contract.md"
      ]
    }
  ]
}
```

### TP 2 — Task-orchestrator runtime reconciliation

```json
{
  "id": "TP-DMX-TASKORCH-RUNTIME-001",
  "project": "dopemux",
  "target": "RUNTIME_VERIFY: reconcile task-orchestrator Docker entrypoint and port authority",
  "invariants": [
    "Task-orchestrator owns workflow transitions, not all PM state",
    "DopeconBridge remains adapter/proxy, not workflow authority",
    "No workflow persistence migration without separate TP"
  ],
  "depends_on": [
    "TP-DMX-RUNTIME-VERIFY-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-RUNTIME-VERIFY-001",
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "fix/task-orchestrator-runtime"
  },
  "commit": {
    "message": "Reconcile task-orchestrator runtime entrypoint and port",
    "allowlist": [
      "services/task-orchestrator/Dockerfile",
      "services/task-orchestrator/app/main.py",
      "services/task-orchestrator/task_orchestrator/app.py",
      "compose.yml",
      "docker/compose.core.yml",
      "services/registry.yaml",
      "tests/unit/test_task_orchestrator_runtime_config.py",
      "15_SYSTEM_TaskOrchestrator.md",
      "04_system-boundaries.md"
    ],
    "verify": [
      "python -m pytest -q tests/unit/test_task_orchestrator_runtime_config.py",
      "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system task-orchestrator --check static"
    ]
  },
  "pr": {
    "title": "Reconcile task-orchestrator runtime entrypoint and port",
    "body": "Aligns task-orchestrator runtime entrypoint and port references or marks unresolved runtime authority explicitly with tests and docs.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Trace task-orchestrator runtime launch paths and port references across Dockerfile, compose files, registry, app code, adapters, and docs.",
      "requirements": [
        "Do not change files in this step",
        "Classify each path as active, legacy, conflicting, or UNKNOWN"
      ],
      "commands": [
        "rg -n \"task_orchestrator\\.app|app/main|3014|8000|task-orchestrator\" services/task-orchestrator compose.yml docker/compose.core.yml services/registry.yaml src tests docs -S"
      ],
      "validation": [
        "Evidence list names every conflicting path",
        "No file modifications occur in S1"
      ],
      "context_files": [
        "15_SYSTEM_TaskOrchestrator.md",
        "12_PM_PLANE.md",
        "10_TRUTH_GAPS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Apply the smallest safe alignment: either fix Docker/compose to launch the active app runtime or mark the conflict fail-closed if runtime proof is insufficient.",
      "requirements": [
        "Do not alter PM authority split",
        "Do not introduce a task-orchestrator local PM database"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_task_orchestrator_runtime_config.py"
      ],
      "expected_files": [
        "services/task-orchestrator/Dockerfile",
        "tests/unit/test_task_orchestrator_runtime_config.py"
      ],
      "validation": [
        "Test proves Docker target does not point at hard-failing legacy module",
        "Port expectation is explicit and single-valued or marked CONFLICTING"
      ],
      "context_files": [
        "15_SYSTEM_TaskOrchestrator.md"
      ]
    },
    {
      "id": "S3",
      "task": "Patch task-orchestrator and boundary docs to reflect the verified or still-conflicting runtime state.",
      "requirements": [
        "Preserve unresolved truth as CONFLICTING or UNKNOWN",
        "Do not claim completion without validation evidence"
      ],
      "commands": [
        "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system task-orchestrator --check static"
      ],
      "expected_files": [
        "15_SYSTEM_TaskOrchestrator.md",
        "04_system-boundaries.md"
      ],
      "validation": [
        "Docs no longer contain contradictory unqualified runtime authority claims",
        "Verifier output is captured for proof bundle"
      ],
      "context_files": [
        "01_RULES.md",
        "04_system-boundaries.md"
      ]
    }
  ]
}
```

### TP 3 — PM endpoint authority tests

```json
{
  "id": "TP-DMX-PM-PORTS-001",
  "project": "dopemux",
  "target": "RUNTIME_VERIFY: add PM endpoint and canonical-writer consistency tests",
  "invariants": [
    "PM metadata writes remain Leantime authority",
    "Workflow transitions remain task-orchestrator authority",
    "Progress and decision logging remain ConPort authority",
    "dope-memory remains historical receipt sink"
  ],
  "depends_on": [
    "TP-DMX-RUNTIME-VERIFY-001",
    "TP-DMX-TASKORCH-RUNTIME-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AUTHORITY-001",
    "base_branch": "main",
    "parent_tp_id": "TP-DMX-TASKORCH-RUNTIME-001",
    "final_packet": true
  },
  "execution": {
    "agent": "codex",
    "branch": "test/pm-authority-ports"
  },
  "commit": {
    "message": "Add PM canonical writer and endpoint consistency tests",
    "allowlist": [
      "src/dopemux/pm/reads.py",
      "src/dopemux/pm/writes.py",
      "src/dopemux/pm/adapters/",
      "tests/unit/test_pm_authority_endpoints.py",
      "12_PM_PLANE.md"
    ],
    "verify": [
      "python -m pytest -q tests/unit/test_pm_authority_endpoints.py",
      "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
    ]
  },
  "pr": {
    "title": "Add PM canonical writer and endpoint consistency tests",
    "body": "Adds tests and documentation to prevent PM metadata, workflow, decision/progress, and historical receipt writers from drifting across endpoints.",
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
      "task": "Inventory PM read/write adapters and endpoint defaults for Leantime, task-orchestrator, ConPort, and dope-memory.",
      "requirements": [
        "Do not edit code in S1",
        "Classify each adapter by canonical writer"
      ],
      "commands": [
        "rg -n \"LEANTIME|CONPORT|TASK_ORCHESTRATOR|DOPE_MEMORY|3014|3004|3005|3020|8000\" src/dopemux/pm services/task-orchestrator tests -S"
      ],
      "validation": [
        "Inventory names every endpoint default and canonical writer"
      ],
      "context_files": [
        "12_PM_PLANE.md",
        "01_RULES.md"
      ]
    },
    {
      "id": "S2",
      "task": "Add unit tests that assert PM write classes route to the declared canonical systems and that mirror writes are labeled as mirrors.",
      "requirements": [
        "No external network dependency",
        "Use stub clients where needed"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_pm_authority_endpoints.py"
      ],
      "expected_files": [
        "tests/unit/test_pm_authority_endpoints.py"
      ],
      "validation": [
        "Tests fail if workflow transitions route directly to Leantime as canonical",
        "Tests fail if dope-memory receipt writes are labeled canonical PM state"
      ],
      "context_files": [
        "12_PM_PLANE.md"
      ]
    },
    {
      "id": "S3",
      "task": "Patch PM_PLANE with endpoint contract, validation commands, and remaining UNKNOWNs.",
      "requirements": [
        "Do not hide ConPort 3004/3005 split unless code is fixed",
        "Do not imply unified PM reader exists"
      ],
      "commands": [
        "python -m pytest -q tests/unit/test_pm_authority_endpoints.py"
      ],
      "expected_files": [
        "12_PM_PLANE.md"
      ],
      "validation": [
        "PM_PLANE includes canonical writer table and command-level validation",
        "Known unresolved endpoint splits remain explicit"
      ],
      "context_files": [
        "12_PM_PLANE.md",
        "10_TRUTH_GAPS.md"
      ]
    }
  ]
}
```

---

## 24. Top 3 doc/gap TPs

### TP 1 — Docs trust map and docs-vs-runtime diff

```json
{
  "id": "TP-DMX-DOC-TRUST-001",
  "project": "dopemux",
  "target": "DOC_CREATE: create DOC_TRUST_MAP.md and DOCS_VS_REPO_DIFF.md from runtime-backed documentation audit",
  "invariants": [
    "Runtime code/config/tests outrank docs",
    "Generated docs remain advisory",
    "Do not rewrite runtime files in a documentation audit"
  ],
  "depends_on": [
    "TP-DMX-RUNTIME-VERIFY-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-DOC-REPAIR-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "docs/trust-map-runtime-diff"
  },
  "commit": {
    "message": "Create docs trust map and docs-vs-runtime diff",
    "allowlist": [
      "docs/03-reference/governance/DOC_TRUST_MAP.md",
      "docs/03-reference/governance/DOCS_VS_REPO_DIFF.md"
    ],
    "verify": [
      "test -f docs/03-reference/governance/DOC_TRUST_MAP.md",
      "test -f docs/03-reference/governance/DOCS_VS_REPO_DIFF.md",
      "rg -n \"DO NOT TRUST|UNKNOWN|CONFLICTING|P0|P1\" docs/03-reference/governance/DOC_TRUST_MAP.md docs/03-reference/governance/DOCS_VS_REPO_DIFF.md"
    ]
  },
  "pr": {
    "title": "Create docs trust map and docs-vs-runtime diff",
    "body": "Adds governance docs that classify documentation reliability and runtime drift without changing runtime code.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "docgen",
      "challenge",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Audit current docs against runtime authority verifier outputs and existing truth docs.",
      "requirements": [
        "No runtime edits",
        "Every mismatch must have severity and source path"
      ],
      "commands": [
        "python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static"
      ],
      "validation": [
        "Audit input includes verifier output and truth docs"
      ],
      "context_files": [
        "01_RULES.md",
        "10_TRUTH_GAPS.md",
        "31_RUNTIME_AUTHORITY_POINTERS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Create DOC_TRUST_MAP.md with HIGH, MEDIUM, LOW, and DO NOT TRUST classifications.",
      "requirements": [
        "Generated docs must be classified advisory or generated",
        "Docs with runtime conflicts must not be HIGH"
      ],
      "expected_files": [
        "docs/03-reference/governance/DOC_TRUST_MAP.md"
      ],
      "validation": [
        "Every primary doc family is classified",
        "Reasons and recommended usage are included"
      ],
      "context_files": [
        "32_CHATGPT_PROJECT_UPLOAD_SET.md"
      ]
    },
    {
      "id": "S3",
      "task": "Create DOCS_VS_REPO_DIFF.md with claim, repo truth, mismatch type, severity, and required TP.",
      "requirements": [
        "Do not normalize contradictions",
        "Use UNKNOWN where runtime proof is absent"
      ],
      "expected_files": [
        "docs/03-reference/governance/DOCS_VS_REPO_DIFF.md"
      ],
      "validation": [
        "P0 drift includes task-orchestrator, ConPort, bridge authority, PM ports, memory transport",
        "No row says no issues"
      ],
      "context_files": [
        "04_system-boundaries.md",
        "12_PM_PLANE.md",
        "15_SYSTEM_TaskOrchestrator.md",
        "16_SYSTEM_ConPort.md"
      ]
    }
  ]
}
```

### TP 2 — Gemini ConPort/task-orchestrator cross-audit

```json
{
  "id": "TP-DMX-GAP-CROSSAUDIT-001",
  "project": "dopemux",
  "target": "AUTHORITY_RESOLUTION: Gemini cross-audit of ConPort and task-orchestrator authority conflicts",
  "invariants": [
    "Gemini audit must not modify files",
    "Conflicts must remain unresolved unless runtime evidence proves resolution",
    "Bridge/proxy surfaces must not be promoted to canonical authority"
  ],
  "depends_on": [],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-GAP-AUDIT-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "gemini",
    "branch": "audit/gemini-authority-crosscheck"
  },
  "commit": {
    "message": "Add Gemini authority cross-audit report",
    "allowlist": [
      "docs/03-reference/governance/GEMINI_AUTHORITY_CROSS_AUDIT.md"
    ],
    "verify": [
      "test -f docs/03-reference/governance/GEMINI_AUTHORITY_CROSS_AUDIT.md",
      "rg -n \"CONFLICTING|UNKNOWN|task-orchestrator|ConPort|P0\" docs/03-reference/governance/GEMINI_AUTHORITY_CROSS_AUDIT.md"
    ]
  },
  "pr": {
    "title": "Add Gemini authority cross-audit report",
    "body": "Adds a read-only Gemini cross-audit report for task-orchestrator and ConPort authority conflicts.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "challenge",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Audit task-orchestrator authority claims across truth docs, system docs, Dockerfile, compose, registry, and PM plane.",
      "requirements": [
        "Read-only audit",
        "Separate OBSERVED, CONFLICTING, UNKNOWN, and RECOMMENDED"
      ],
      "commands": [
        "rg -n \"task-orchestrator|task_orchestrator|3014|8000|workflow_store|workflow_ideas|workflow_epics\" . -S"
      ],
      "validation": [
        "Report includes claim A, claim B, evidence, risk, and unresolved resolution state"
      ],
      "context_files": [
        "15_SYSTEM_TaskOrchestrator.md",
        "12_PM_PLANE.md",
        "10_TRUTH_GAPS.md"
      ]
    },
    {
      "id": "S2",
      "task": "Audit ConPort authority claims across truth docs, system docs, Docker runtime docs, src runtime docs, and PM plane.",
      "requirements": [
        "Do not choose a runtime without runtime evidence",
        "List all candidate canonical surfaces"
      ],
      "commands": [
        "rg -n \"ConPort|conport|memory_server|enhanced_server|3004|3005|4004\" . -S"
      ],
      "validation": [
        "Report names Docker and src candidates and classifies confidence"
      ],
      "context_files": [
        "05_TRUTH_SCOPE.md",
        "09_TRUTH_CANONICALS.md",
        "16_SYSTEM_ConPort.md"
      ]
    },
    {
      "id": "S3",
      "task": "Write cross-audit report with exact next source-pull and runtime-verification requirements.",
      "requirements": [
        "No docs rewritten except the audit report",
        "Every recommendation includes validation and risk"
      ],
      "expected_files": [
        "docs/03-reference/governance/GEMINI_AUTHORITY_CROSS_AUDIT.md"
      ],
      "validation": [
        "Report contains Top 3 P0 blockers and exact follow-up TPs",
        "Report preserves unresolved conflicts"
      ],
      "context_files": [
        "01_RULES.md",
        "23_PAL_EXECUTION_RULES.md"
      ]
    }
  ]
}
```

### TP 3 — Agent instruction creation

```json
{
  "id": "TP-DMX-AGENTS-CREATE-001",
  "project": "dopemux",
  "target": "AGENT_INSTRUCTION_CREATE: create deterministic Copilot agent specs for planner, implementer, reviewer, and testgen",
  "invariants": [
    "Agents do not own PM truth, memory truth, retrieval truth, or bridge authority",
    "Agents must follow TP allowlists",
    "Planner and reviewer agents must not have edit tools"
  ],
  "depends_on": [
    "TP-DMX-DOC-TRUST-001"
  ],
  "repo_binding": {
    "project_id": "dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "dopemux-mvp",
    "require_identity_match": true
  },
  "series": {
    "id": "SERIES-DMX-AGENTS-001",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": true
  },
  "execution": {
    "agent": "codex",
    "branch": "agents/dopemux-copilot-agent-specs"
  },
  "commit": {
    "message": "Create deterministic Dopemux Copilot agent specs",
    "allowlist": [
      ".github/agents/dopemux-planner.agent.md",
      ".github/agents/dopemux-implementer.agent.md",
      ".github/agents/dopemux-reviewer.agent.md",
      ".github/agents/dopemux-testgen.agent.md",
      "docs/03-reference/governance/AGENT_WORKFLOW.md"
    ],
    "verify": [
      "test -f .github/agents/dopemux-planner.agent.md",
      "test -f .github/agents/dopemux-implementer.agent.md",
      "test -f .github/agents/dopemux-reviewer.agent.md",
      "test -f .github/agents/dopemux-testgen.agent.md",
      "rg -n \"tools:|description:|handoffs:|Do not\" .github/agents/*.agent.md"
    ]
  },
  "pr": {
    "title": "Create deterministic Dopemux Copilot agent specs",
    "body": "Adds scoped Copilot agent profiles for Dopemux planning, implementation, review, and test generation with architecture boundary guardrails.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "planner",
      "docgen",
      "challenge",
      "codereview",
      "precommit"
    ]
  },
  "steps": [
    {
      "id": "S1",
      "task": "Create planner and reviewer agent specs with read/search-only tools and explicit authority-boundary rules.",
      "requirements": [
        "Use .agent.md frontmatter",
        "Planner and reviewer must not have edit or execute tools"
      ],
      "expected_files": [
        ".github/agents/dopemux-planner.agent.md",
        ".github/agents/dopemux-reviewer.agent.md"
      ],
      "validation": [
        "Planner and reviewer include tools without edit/execute",
        "Both mention no bridge/retrieval/mirror promotion"
      ],
      "context_files": [
        "40_agents.instructions.md",
        "22_AGENTS.md",
        "01_RULES.md"
      ]
    },
    {
      "id": "S2",
      "task": "Create implementer and testgen agent specs with scoped tool access and TP allowlist enforcement.",
      "requirements": [
        "Implementer may edit only TP allowlist",
        "Testgen may edit tests only unless TP explicitly allows production code"
      ],
      "expected_files": [
        ".github/agents/dopemux-implementer.agent.md",
        ".github/agents/dopemux-testgen.agent.md"
      ],
      "validation": [
        "Implementer requires repo/worktree verification before edits",
        "Testgen forbids unrelated production edits"
      ],
      "context_files": [
        "23_PAL_EXECUTION_RULES.md",
        "26_dopetask-cannonical-spec.json"
      ]
    },
    {
      "id": "S3",
      "task": "Document deterministic agent handoff workflow.",
      "requirements": [
        "No more than 2-3 handoffs per agent",
        "Document stop conditions and proof requirements"
      ],
      "expected_files": [
        "docs/03-reference/governance/AGENT_WORKFLOW.md"
      ],
      "validation": [
        "Workflow doc maps planner to implementer to reviewer to testgen",
        "Workflow doc states agents are helpers, not authorities"
      ],
      "context_files": [
        "37_handoff-contract.md",
        "36_proof-contract.md"
      ]
    }
  ]
}
```

---

## 25. Validation strategy

| Validation layer         | Exact checks                                                                         | Pass condition                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| TP schema                | `python -m jsonschema 26_dopetask-cannonical-spec.json <packet>.json`                | No schema errors; Gemini packets include enabled PAL chain.                                     |
| Worktree preflight       | `git rev-parse --show-toplevel`; marker check; branch check; primary checkout check. | Dedicated worktree, correct branch, marker exists.                                              |
| Runtime authority static | `python scripts/verify_runtime_authority.py --check static`                          | Known conflicts reported deterministically; unexpected drift fails.                             |
| Runtime smoke            | Service-specific `/health`, CLI help, wrapper help.                                  | Expected service answers on declared port/path.                                                 |
| PM authority             | Unit tests for writer classification.                                                | Metadata→Leantime, workflow→task-orchestrator, progress/decision→ConPort, receipts→dope-memory. |
| Bridge boundary          | Route-to-writer table test/static scan.                                              | Every bridge write names upstream canonical writer.                                             |
| Retrieval discipline     | dope-context tests + doc grep.                                                       | Docs say derived, not truth; code/docs hits trace to source.                                    |
| Data/events              | Event envelope schema tests.                                                         | Required fields present; idempotency via `event_id`.                                            |
| Redaction                | Secret scanner before storage and promotion.                                         | No known secret patterns in artifacts.                                                          |
| Proof                    | Proof bundle/handoff validators.                                                     | Manifest, warnings/blockers, chain of custody present.                                          |
| Performance              | Service tests for `p50 < 50ms`, `p99 < 250ms` where applicable.                      | No regression beyond target or explicit waiver.                                                 |
| Final gate               | codereview + precommit + PR.                                                         | Diff reviewed, tests pass, PR opened, worktree cleanup recorded.                                |

“No issues” is invalid. A passing validation report must name what was checked, what passed, what remains risky, and what was not tested. Because apparently we need to tell machines not to fake confidence, which is rich. 🧾

---

## 26. Risk register

| Risk                               | Severity | Cause                                               | Mitigation                      | TP               |
| ---------------------------------- | -------: | --------------------------------------------------- | ------------------------------- | ---------------- |
| Wrong workflow runtime deployed    |       P0 | task-orchestrator Docker/app/port conflict          | Runtime reconciliation          | TASKORCH-RUNTIME |
| Wrong ConPort surface used         |       P0 | Docker vs `src/conport` conflict                    | Cross-audit + runtime proof     | CONPORT-AUTH     |
| Bridge becomes de facto authority  |       P0 | Broad proxy route surface                           | Route-to-writer matrix          | BRIDGE-WRITER    |
| PM writes hit wrong endpoints      |       P0 | Port/default drift                                  | PM endpoint tests               | PM-PORTS         |
| Memory calls target stale WMA port |       P1 | `8096` legacy adapter                               | Transport deprecation/fix       | MEMORY-TRANSPORT |
| Dopemux CLI unusable               |       P1 | Reported import failure                             | Reproduce/fix                   | CLI-VERIFY       |
| Agent sprawl mutates wrong plane   |       P1 | No canonical agent authority                        | Scoped agent specs              | AGENTS-CREATE    |
| Generated docs stale               |       P2 | Upload set is snapshot                              | Regenerate manifest             | UPLOAD-REFRESH   |
| Unsafe docs leak secrets           |       P1 | Secret-pattern skipped docs                         | Redacted pull and scanner       | SECRET-REDACT    |
| Proof contracts unenforced         |       P1 | Contracts exist as prose                            | Validators/gates                | PROOF-GATE       |
| Retrieval treated as truth         |       P0 | dope-context/ConPort search outputs look convenient | Retrieval discipline tests/docs | CONTEXT-WRAPPER  |
| Postgres mirror treated canonical  |       P0 | Mirror is easier to query                           | SQLite-first validation         | MEMORY-TRANSPORT |

---

## 27. First packet series

**Series:** `SERIES-DMX-AUTHORITY-001`

| Order | Packet                        | Purpose                                                      | Stop condition                                                                                           |
| ----: | ----------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
|     1 | `TP-DMX-RUNTIME-VERIFY-001`   | Build deterministic authority verifier.                      | Missing repo marker, unknown base branch, or verifier cannot distinguish expected conflict from failure. |
|     2 | `TP-DMX-TASKORCH-RUNTIME-001` | Fix or explicitly fail-close task-orchestrator runtime/port. | Docker boot evidence unavailable or runtime choice requires human decision.                              |
|     3 | `TP-DMX-PM-PORTS-001`         | Lock PM canonical-writer and endpoint tests.                 | ConPort authority unresolved enough to make tests dishonest.                                             |

**Series branch scope:** one dedicated worktree, branch per TP or scoped branch per series, no primary checkout edits.

**Required first commands:**

```bash
git rev-parse --show-toplevel
test -e .dopetaskroot
git status --short
git branch --show-current
git remote -v
```

**Proof required at end:**

| Proof item           | Required                                |
| -------------------- | --------------------------------------- |
| Slices completed     | Yes                                     |
| Validations run      | Yes, with command output and exit codes |
| Risks                | Yes, residual risk table                |
| PR URL               | Yes after PR opened                     |
| Worktree path        | Yes                                     |
| Verified branch      | Yes                                     |
| Repo identity result | Yes                                     |
| Cleanup status       | Yes, removed or blocked with reason     |

**What must wait:** ConPort doc promotion, PM endpoint finalization, and agent workflow automation must wait until runtime authority verification completes. Otherwise the system will elegantly automate the wrong facts, which is the fanciest kind of failure. 🎩

---

## 28. Final operating model

Dopemux should operate as a **deterministic, evidence-gated, multi-agent execution system**:

| Layer                 | Operating rule                                                                                                                          |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| ChatGPT supervisor    | Extract truth, generate TPs, maintain doc/gap backlog, never claim runtime execution.                                                   |
| Codex implementer     | Execute approved TPs in fresh worktrees, commit-sized slices, with proof.                                                               |
| Claude reviewer       | Challenge diffs, docs, and architecture boundaries.                                                                                     |
| Claude Code local dev | Explore/review interactively with bounded subagents.                                                                                    |
| Copilot custom agents | Provide IDE/cloud-agent planner/implementer/reviewer/testgen roles with strict tool limits.                                             |
| Gemini auditor        | Cross-audit contradictions and source gaps with required PAL chain.                                                                     |
| Dopemux repo          | Remains multi-plane: control, execution, PM, memory, retrieval, bridge, operator support, extraction.                                   |
| Truth system          | Runtime > `TRUTH_*` > canonical docs > system docs > contracts > generated docs.                                                        |
| State system          | Events/evidence only; canonical writer named before write; mirrors and retrieval never promoted.                                        |
| Operator UX           | Default state summaries use Top-3 `items`, `more_count`, `next_token`; Telegram Topics remain primary UI boundary for approvals/errors. |

**Final verdict:** build the system around **authority verification first**, then repair docs, then add agent automation. Anything else is just giving more tools to a confused architecture, which is how civilizations get Kubernetes dashboards nobody understands.

[1]: https://help.openai.com/en/articles/10169521-projects-in-chatgpt?utm_source=chatgpt.com "Projects in ChatGPT"
[2]: https://docs.anthropic.com/en/docs/claude-code/sub-agents?utm_source=chatgpt.com "Create custom subagents - Claude Code Docs"
[3]: https://docs.github.com/en/copilot/reference/custom-agents-configuration?utm_source=chatgpt.com "Custom agents configuration"
[4]: https://ai.google.dev/gemini-api/docs/coding-agents?utm_source=chatgpt.com "Set up your coding assistant with Gemini MCP and Skills"
[5]: https://developers.openai.com/codex/app?utm_source=chatgpt.com "Codex app"
[6]: https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents?utm_source=chatgpt.com "Creating custom agents for Copilot cloud agent"

