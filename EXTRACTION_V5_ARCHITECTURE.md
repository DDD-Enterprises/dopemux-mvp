# DopeMux Truth Extractor v5 - Comprehensive Phase Architecture

## PHASES Constant
**Location:** Line 176
```python
PHASES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S"]
```

## R_REQUIRED_INPUT_PHASES & R_REQUIRED_ARTIFACT_GROUPS
**Location:** Lines 285-331

### R_REQUIRED_INPUT_PHASES
```python
R_REQUIRED_INPUT_PHASES = ["A", "H", "D", "C"]
```

### R_REQUIRED_ARTIFACT_GROUPS (Phase → Artifact Groups)
- **Phase A** (10 artifact groups):
  - REPO_INSTRUCTION_SURFACE.json
  - REPO_INSTRUCTION_REFERENCES.json
  - REPO_MCP_SERVER_DEFS.json
  - REPO_MCP_PROXY_SURFACE.json
  - REPO_ROUTER_SURFACE.json
  - REPO_HOOKS_SURFACE.json
  - REPO_IMPLICIT_BEHAVIOR_HINTS.json
  - REPO_COMPOSE_SERVICE_GRAPH.json
  - REPO_LITELLM_SURFACE.json
  - REPO_TASKX_SURFACE.json

- **Phase H** (7 artifact groups):
  - HOME_MCP_SURFACE.json
  - HOME_ROUTER_SURFACE.json
  - HOME_PROVIDER_LADDER_HINTS.json
  - HOME_LITELLM_SURFACE.json
  - HOME_PROFILES_SURFACE.json
  - HOME_TMUX_WORKFLOW_SURFACE.json
  - HOME_SQLITE_SCHEMA.json

- **Phase D** (5 artifact groups):
  - DOC_TOPIC_CLUSTERS.json
  - DOC_SUPERSESSION.json
  - DOC_CONTRACT_CLAIMS.json
  - (DUPLICATE_DRIFT_REPORT.json OR DOC_RECENCY_DUPLICATE_REPORT.json)
  - DOC_INDEX.json

- **Phase C** (13 artifact groups):
  - SERVICE_ENTRYPOINTS.json
  - EVENTBUS_SURFACE.json
  - EVENT_PRODUCERS.json
  - EVENT_CONSUMERS.json
  - DOPE_MEMORY_CODE_SURFACE.json
  - DOPE_MEMORY_SCHEMAS.json
  - DOPE_MEMORY_DB_WRITES.json
  - TRINITY_ENFORCEMENT_SURFACE.json
  - REFUSAL_AND_GUARDRAILS_SURFACE.json
  - TASKX_INTEGRATION_SURFACE.json
  - WORKFLOW_RUNNER_SURFACE.json
  - DETERMINISM_RISK_LOCATIONS.json
  - IDEMPOTENCY_RISK_LOCATIONS.json
  - CONCURRENCY_RISK_LOCATIONS.json

---

## REQUIRED_PROMPT_STEP_IDS (per Phase)
**Location:** Lines 1018-1034

- **A**: {A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A99} (15 steps)
- **H**: {H0, H1, H2, H3, H4, H5, H6, H7, H9} (9 steps)
- **D**: {D0, D1, D2, D3, D4, D5} (6 steps)
- **C**: {C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17} (18 steps)
- **E**: {E0, E1, E2, E3, E4, E5, E6, E9} (8 steps)
- **W**: {W0, W1, W2, W3, W4, W5, W9} (7 steps)
- **B**: {B0, B1, B2, B3, B9} (5 steps)
- **G**: {G0, G1, G2, G3, G4, G9} (6 steps)
- **Q**: {Q0, Q1, Q2, Q3, Q9} (5 steps)
- **R**: {R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10} (11 steps)
- **X**: {X0, X1, X2, X3, X4, X9} (6 steps)
- **T**: {T0, T1, T2, T3, T4, T5, T9} (7 steps)
- **Z**: {Z0, Z1, Z2, Z9} (4 steps)
- **S**: {S0, S1, S2, S3, S4, S5, S6} (7 steps)

---

## DETAILED PHASE MAPPING

### PHASE A: Repo Control Plane
**Handler:** `run_phase_A()` at line 14158
**Description:** Scans repo control plane — instructions, MCP configs, routers, hooks, compose, LiteLLM, TaskX

**Targets Scanned (Collector Pattern):**
- Excludes: .git, node_modules, venv, .venv, tests, docs, extraction, reports, tmp, _audit_out, SYSTEM_ARCHIVE
- Directories: .claude, .dopemux, .githooks, .github, .taskx, config, scripts, tools, compose, docker
- Files: AGENTS.md, README.md, QUICK_START.md, INSTALL.md, CHANGELOG.md, pyproject.toml, dopemux.toml, compose.yml, Makefile, .claude.json, .taskxroot
- Subdirs: .vibe, src/dopemux/hooks, src/dopemux/claude, src/dopemux/claude_tools, src/dopemux/commands, src/dopemux/mcp, src/dopemux/cli.py, src/dopemux/__main__.py, src/dopemux/routing_cli.py, src/dopemux/profile_commands.py, src/dopemux/dev_commands.py, src/dopemux/worktree_commands.py, src/dopemux/events, src/dopemux/event_bus.py, services/copilot_transcript_ingester, services/dopecon-bridge, mcp-proxy-config files

**Partitions:** Built via `build_partitions()` from collector items (artifact-aggregation method)

**Output Artifacts by Step:**
- **A0**: REPOCTRL_INVENTORY.json, REPOCTRL_PARTITIONS.json (inventory/partitioning)
- **A1**: REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json
- **A2**: REPO_MCP_SERVER_DEFS.json
- **A3**: REPO_MCP_PROXY_SURFACE.json
- **A4**: REPO_ROUTER_SURFACE.json
- **A5**: REPO_HOOKS_SURFACE.json
- **A6**: REPO_COMPOSE_SERVICE_GRAPH.json
- **A7**: REPO_LITELLM_SURFACE.json
- **A8**: REPO_TASKX_SURFACE.json
- **A9**: REPO_IMPLICIT_BEHAVIOR_HINTS.json
- **A10**: REPO_LEANTIME_SURFACE.json
- **A11**: EDITOR_INTEGRATION_SURFACE.json
- **A12**: CLI_COMMAND_SURFACE.json
- **A13**: HOOK_CONTRACT_SURFACE.json, EVENT_FLOW_GRAPH.json
- **A99** (merge/QA): REPO_INSTRUCTION_SURFACE.json, REPO_INSTRUCTION_REFERENCES.json, REPO_MCP_SERVER_DEFS.json, REPO_MCP_PROXY_SURFACE.json, REPO_ROUTER_SURFACE.json, REPO_HOOKS_SURFACE.json, REPO_IMPLICIT_BEHAVIOR_HINTS.json, REPO_COMPOSE_SERVICE_GRAPH.json, REPO_LITELLM_SURFACE.json, REPO_LEANTIME_SURFACE.json, REPO_TASKX_SURFACE.json, REPOCTRL_NORM_MANIFEST.json, REPOCTRL_QA.json

**Hard Dependencies:** None
**Soft Dependencies:** None (first extraction phase)

---

### PHASE H: Home Control Plane
**Handler:** `run_phase_H()` at line 14230
**Description:** Scans home directory safe roots (user config, profiles, MCP configs, LiteLLM, TaskX, schemas)

**Safe Roots (HOME_SAFE_ROOTS):**
- .dopemux, .config/dopemux, .config/taskx, .config/litellm, .config/mcp

**Allowed Suffixes:** .yaml, .yml, .toml, .json, .md, .txt, .ini, .cfg, .conf

**Denied Globs:** *.db, *.sqlite, *.sqlite3, *.log, *.cache, *.tmp, *.swp, *cache*, *logs*, *.pem, *.p12, *.pfx, *.der, *.crt, *key*, *token*, *secret*, *pass*, *credential*

**Partitions:** Built via precollected_items (from Collector.collect(subdirs=HOME_SAFE_ROOTS)) → `build_partitions()`

**Output Artifacts by Step:**
- **H0**: HOME_INVENTORY.json, HOME_PARTITIONS.json (inventory/partitioning)
- **H1**: HOME_KEYS_SURFACE.json, HOME_REFERENCES.json
- **H2**: HOME_MCP_SURFACE.json
- **H3**: HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json
- **H4**: HOME_LITELLM_SURFACE.json
- **H5**: HOME_PROFILES_SURFACE.json
- **H6**: HOME_TMUX_WORKFLOW_SURFACE.json
- **H7**: HOME_SQLITE_SCHEMA.json
- **H9** (merge/QA): HOMECTRL_NORM_MANIFEST.json, HOMECTRL_QA.json, HOME_KEYS_SURFACE.json, HOME_REFERENCES.json, HOME_MCP_SURFACE.json, HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json, HOME_LITELLM_SURFACE.json, HOME_PROFILES_SURFACE.json, HOME_TMUX_WORKFLOW_SURFACE.json, HOME_SQLITE_SCHEMA.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE D: Docs Pipeline
**Handler:** `run_phase_D()` at line 14284
**Description:** Scans /docs directory — documentation, claims, supersession analysis, contract analysis

**Targets Scanned:**
- Excludes: .git
- Directories: docs

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **D0**: DOC_INVENTORY.json, DOC_PARTITIONS.json, DOC_TODO_QUEUE.json (inventory/partitioning)
- **D1**: DOC_INDEX.partX.json, DOC_CONTRACT_CLAIMS.partX.json, DOC_BOUNDARIES.partX.json, DOC_SUPERSESSION.partX.json, CAP_NOTICES.partX.json (partitioned outputs)
- **D2**: DOC_INTERFACES.partX.json, DOC_WORKFLOWS.partX.json, DOC_DECISIONS.partX.json, DOC_GLOSSARY.partX.json (partitioned outputs)
- **D3**: DOC_CITATION_GRAPH.json
- **D4** (merge/aggregate): DOC_INDEX.json, DOC_CONTRACT_CLAIMS.json, DOC_SUPERSESSION.json, DOC_TOPIC_CLUSTERS.json, DUPLICATE_DRIFT_REPORT.json, DOC_RECENCY_DUPLICATE_REPORT.json, DOC_COVERAGE_REPORT.json
- **D5**: DOC_TOPIC_CLUSTERS.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE C: Code Surfaces
**Handler:** `run_phase_C()` at line 14262
**Description:** Scans code architecture — service entrypoints, event bus, memory patterns, boundaries, integration, workflows, determinism/idempotency risks

**Targets Scanned:**
- Excludes: .git, node_modules, venv, .venv, docs, test-results
- Directories: src, services, shared, plugins, tools, scripts, tests

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **C0**: CODE_INVENTORY.json, CODE_PARTITIONS.json (inventory/partitioning)
- **C1**: SERVICE_ENTRYPOINTS.json
- **C2**: EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- **C3**: DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- **C4**: TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json
- **C5**: TASKX_INTEGRATION_SURFACE.json
- **C6**: WORKFLOW_RUNNER_SURFACE.json
- **C7**: API_DASHBOARD_SURFACE.json
- **C8**: DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, SECRETS_RISK_LOCATIONS.json
- **C9** (merge/aggregate): SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json, DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json, TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json, TASKX_INTEGRATION_SURFACE.json, WORKFLOW_RUNNER_SURFACE.json, LEANTIME_INTEGRATION_SURFACE.json, DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json, CODE_SURFACES_QA.json, SERVICE_CATALOG.json, AGENT_ORCHESTRATION_SURFACE.json, ADHD_ENGINE_SURFACE.json, PYTHON_API_SURFACE.json, SERVICE_ENDPOINT_SURFACE.json, MODULE_DEPENDENCY_GRAPH.json, SERVICE_DEPENDENCY_GRAPH.json, COGNITIVE_FEATURES_SURFACE.json
- **C10**: SERVICE_CATALOG.partX.json (partitioned)
- **C11**: LEANTIME_INTEGRATION_SURFACE.json
- **C12**: AGENT_ORCHESTRATION_SURFACE.json
- **C13**: ADHD_ENGINE_SURFACE.json
- **C14**: CODE_HEALTH_SURFACE.json
- **C15**: DEAD_CODE_INVENTORY.json
- **C16**: MODULE_DEPENDENCY_GRAPH.json, SERVICE_DEPENDENCY_GRAPH.json
- **C17**: COGNITIVE_FEATURES_SURFACE.json

**Hard Dependencies:** None
**Soft Dependencies:** None

**Notes:** C is CODE_HEAVY_PHASE (uses max_files_code limit)

---

### PHASE E: Execution Plane
**Handler:** `run_phase_E()` at line 14299
**Description:** Scans execution infrastructure — bootstrap commands, env chains, startup graphs, runtime modes, artifact surfaces, execution risks

**Targets Scanned:**
- Excludes: .git, node_modules, docs
- Directories: scripts, tools, compose, .github, Makefile, package.json

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **E0**: EXEC_INVENTORY.json, EXEC_PARTITIONS.json (inventory/partitioning)
- **E1**: EXEC_BOOTSTRAP_COMMANDS.json
- **E2**: EXEC_ENV_CHAIN.json
- **E3**: EXEC_STARTUP_GRAPH.json
- **E4**: EXEC_RUNTIME_MODES.json, EXEC_MODE_DELTA_REPORT.json
- **E5**: EXEC_ARTIFACT_SURFACE.json
- **E6**: EXEC_RISK_FACTS.json
- **E9** (merge/aggregate): EXEC_MERGED.json, EXEC_QA.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE W: Workflow Plane
**Handler:** `run_phase_W()` at line 14318
**Description:** Scans workflow orchestration — catalog, I/O maps, coordination, failure recovery, state coupling

**Targets Scanned:**
- Excludes: .git, node_modules
- Directories: docs, scripts, src, services

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **W0**: WORKFLOW_INVENTORY.json, WORKFLOW_PARTITIONS.json (inventory/partitioning)
- **W1**: WORKFLOW_CATALOG.json
- **W2**: WORKFLOW_IO_MAP.json
- **W3**: WORKFLOW_COORDINATION_SURFACE.json
- **W4**: WORKFLOW_FAILURE_RECOVERY.json
- **W5**: WORKFLOW_STATE_COUPLING.json
- **W9** (merge/QA): WORKFLOW_MERGED.json, WORKFLOW_QA.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE B: Boundary Plane
**Handler:** `run_phase_B()` at line 14335
**Description:** Scans boundary enforcement — boundary points, refusal guardrails, bypass risks

**Targets Scanned:**
- Excludes: .git, node_modules
- Directories: src, services, docs

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **B0**: BOUNDARY_INVENTORY.json, BOUNDARY_PARTITIONS.json (inventory/partitioning)
- **B1**: BOUNDARY_ENFORCEMENT_POINTS.json
- **B2**: REFUSAL_GUARDRAILS_SURFACE.json
- **B3**: BOUNDARY_BYPASS_RISKS.json
- **B9** (merge/QA): BOUNDARY_MERGED.json, BOUNDARY_QA.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE G: Governance Plane
**Handler:** `run_phase_G()` at line 14352
**Description:** Scans governance & policies — CI gates, hygiene policies, secrets, policy enforcement

**Targets Scanned:**
- Excludes: .git, node_modules
- Directories: .github, docs, .claude, AGENTS.md

**Partitions:** Built via collector items → `build_partitions()`

**Output Artifacts by Step:**
- **G0**: GOV_INVENTORY.json, GOV_PARTITIONS.json (inventory/partitioning)
- **G1**: GOV_CI_GATES.json
- **G2**: GOV_HYGIENE_POLICIES.json
- **G3**: GOV_POLICIES.json
- **G4**: GOV_SECRETS_SURFACE.json
- **G9** (merge/QA): GOV_MERGED.json, GOV_QA.json

**Hard Dependencies:** None
**Soft Dependencies:** None

---

### PHASE Q: Quality Assurance
**Handler:** `run_phase_Q()` at line 14369
**Description:** Quality gate — collects artifacts from A/H/D/C/E/W/B/G, verifies completeness, detects drift, checks for collisions

**Partitions:** Built via precollected_items (from `collect_phase_artifacts(dirs, ["A", "H", "D", "C", "E", "W", "B", "G"], ["raw", "norm", "qa"])` + Q_PROMPTPACK_DECLARED_OUTPUTS manifest) → `build_partitions()`

**Output Artifacts by Step:**
- **Q0**: QA_RUN_MANIFEST.json
- **Q1**: QA_MISSING_ARTIFACTS.json
- **Q2**: QA_PROMPT_COLLISIONS.json
- **Q3**: QA_NORM_DRIFT_REPORT.json
- **Q9** (merge/QA): PIPELINE_DOCTOR_REPORT.json, QA_SERVICE_COVERAGE.json

**Hard Dependencies:** A, H, D, C, E, W, B, G (reads norm/raw/qa from all)
**Soft Dependencies:** None

**Notes:** Phase Q is special — it directly consumes outputs from 8 prior phases without doing its own file collection. Uses `collect_phase_artifacts()` helper function.

---

### PHASE R: Arbitration (GPT-5.2)
**Handler:** `run_phase_R()` at line 14900
**Description:** High-level synthesis — control plane truth, dope memory, eventbus wiring, boundaries, TaskX, workflows, risks, conflicts, LiteLLM, two-plane architecture

**Partitions:** Built via precollected_items (from norm outputs of A, H, D, C phases) → `build_partitions()`

**Required Inputs (Hard Dependency):**
- Normalized artifacts from Phase A (norm/)
- Normalized artifacts from Phase H (norm/)
- Normalized artifacts from Phase D (norm/)
- Normalized artifacts from Phase C (norm/)

**How Inputs Are Collected:**
```python
for phase in R_REQUIRED_INPUT_PHASES:  # ["A", "H", "D", "C"]
    phase_norm = dirs[phase] / "norm"
    if phase_norm.exists():
        input_files.extend(sorted(phase_norm.glob("*.json")))
        input_files.extend(sorted(phase_norm.glob("*.md")))
```
Inputs are passed as precollected_items to `_run_phase_inner()`.

**Output Artifacts by Step:**
- **R0**: CONTROL_PLANE_TRUTH_MAP.md
- **R1**: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- **R2**: EVENTBUS_WIRING_TRUTH.md
- **R3**: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md
- **R4**: TASKX_INTEGRATION_TRUTH.md
- **R5**: WORKFLOWS_TRUTH_GRAPH.md
- **R6**: PORTABILITY_AND_MIGRATION_RISK_LEDGER.md
- **R7**: CONFLICT_LEDGER.md
- **R8**: RISK_REGISTER_TOP20.md
- **R9**: LEANTIME_INTEGRATION_TRUTH.md
- **R10**: TWO_PLANE_ARCHITECTURE_TRUTH.md

**Hard Dependencies:** A, H, D, C (must have norm artifacts)
**Soft Dependencies:** None

**Async Pilot:** Phase R has async submission variant (`run_phase_R_async_submit()` at line 14482) and finalization (`run_phase_R_finalize()` at line 14733) for OpenAI Responses API webhook integration.

---

### PHASE X: Feature Index
**Handler:** `run_phase_X()` at line 14930
**Description:** Feature surface extraction & indexing — features, code mappings, doc mappings, dependency graphs

**Partitions:** Built via precollected_items (from R norm/) → `build_partitions()`

**Required Inputs (Hard Dependency):**
- Normalized artifacts from Phase R (norm/)

**How Inputs Are Collected:**
```python
r_norm = dirs["R"] / "norm"
if r_norm.exists():
    r_inputs.extend(sorted(r_norm.glob("*.json")))
    r_inputs.extend(sorted(r_norm.glob("*.md")))
```

**Output Artifacts by Step:**
- **X0**: FEATURE_INDEX_INVENTORY.json, FEATURE_INDEX_PARTITIONS.json (inventory/partitioning)
- **X1**: FEATURE_SURFACE.json
- **X2**: FEATURE_CODE_MAP.json
- **X3**: FEATURE_DOC_MAP.json
- **X4**: FEATURE_DEP_GRAPH.json
- **X9** (merge/QA): FEATURE_INDEX_MERGED.json, FEATURE_INDEX_QA.json

**Hard Dependencies:** R (requires norm outputs)
**Soft Dependencies:** None

---

### PHASE T: Task Packets
**Handler:** `run_phase_T()` at line 14952
**Description:** Task packet generation — factory, schema, generation, dedup, collision resolution, ordering, run plan

**Partitions:** Built via precollected_items (from R norm/ + X norm/) → `build_partitions()`

**Required Inputs (Hard Dependency):**
- Normalized artifacts from Phase R (norm/)
- Normalized artifacts from Phase X (norm/)

**How Inputs Are Collected:**
```python
for phase in ["R", "X"]:
    norm_dir = dirs[phase] / "norm"
    if norm_dir.exists():
        input_files.extend(sorted(norm_dir.glob("*.json")))
        input_files.extend(sorted(norm_dir.glob("*.md")))
```

**Output Artifacts by Step:**
- **T0**: PROJECT_INSTRUCTIONS.md, TP_BACKLOG_TOPN.json, TP_INDEX.json
- **T1**: TP_PACKETS_TOP10.partX.md, TP_PACKET_IMPLEMENTATION_INDEX.json, TP_BACKLOG_TOPN.json (partitioned)
- **T2**: TP_SCHEMA.json, TP_AUTHORITY_RULES.json
- **T3**: TP_BATCHED_PACKETS.partX.md, TP_BATCH_INDEX.json (partitioned)
- **T4**: TP_DEDUPED.json, TP_COLLISIONS.json
- **T5**: TP_RUN_PLAN.json, TP_BACKLOG_TOPN.json
- **T9** (merge/QA): TP_INDEX.json, TP_MERGED.json, TP_QA.json, TP_SUMMARY.md, TP_BACKLOG_TOPN.json

**Hard Dependencies:** R, X (must have norm artifacts)
**Soft Dependencies:** None

---

### PHASE Z: Handoff Freeze
**Handler:** `run_phase_Z()` at line 15019
**Description:** Mechanical freeze/checksum phase — consolidates R/X/T outputs, computes checksums, creates proof pack, manifest

**Partitions:** Built via precollected_items (from R/X/T raw/norm/qa/) → `build_partitions()`

**How Inputs Are Collected:**
```python
collect_phase_artifacts(dirs, ["R", "X", "T"], ["raw", "norm", "qa"])
```

**Output Artifacts by Step:**
- **Z0**: FREEZE_FILE_INDEX.json, FREEZE_CHECKSUMS.json
- **Z1**: PROOF_PACK.md
- **Z2**: OPUS_INPUT_MANIFEST.json
- **Z9** (merge/QA): FREEZE_MANIFEST.json, FREEZE_README.md, FREEZE_QA.json

**Hard Dependencies:** R, X, T (must have outputs from all three)
**Soft Dependencies:** None

**Notes:** Z is purely deterministic/mechanical — no LLM processing, just checksumming and manifest consolidation.

---

### PHASE S: Synthesis (GPT-5 Opus)
**Handler:** `run_phase_S()` at line 14973
**Description:** Final synthesis — architecture synthesis, migration plans, decision dossier, proof hooks, truth pack index

**Partitions:** Built via precollected_items (from R/X/T/Z norm/ + manual_rulings/) → `build_partitions()`

**How Inputs Are Collected:**
```python
# Mandatory R inputs
for path in sorted(r_norm.glob("*.json")) + sorted(r_norm.glob("*.md")):
    input_sources[path.resolve()] = "R"

# Optional X/T/Z inputs
for phase in ["X", "T", "Z"]:
    norm_dir = dirs[phase] / "norm"
    if norm_dir.exists():
        for path in sorted(norm_dir.glob("*.json")) + sorted(norm_dir.glob("*.md")):
            input_sources.setdefault(path.resolve(), phase)

# Optional manual rulings
manual_rulings_dir = dirs["root"] / "manual_rulings"
if manual_rulings_dir.exists():
    for path in sorted(manual_rulings_dir.glob("PRO_*.json")):
        input_sources.setdefault(path.resolve(), "MANUAL")
```

**Selected Steps Mode:**
- If `cfg.selected_s_steps` is set, uses those (e.g., [S0, S2, S4])
- Otherwise uses all steps from `_selected_execution_step_ids_for_phase(cfg, "S")`

**Prompts Mode Resolution:**
- Checks `get_phase_prompts("S")` source: "registry" vs "legacy"
- Can load from Phase S registry or fall back to v4 legacy prompts

**Output Artifacts by Step:**
- **S0**: S0_ARCHITECTURE_SYNTHESIS_OPUS.md
- **S1**: S1_MCP_TO_HOOKS_MIGRATION_PLAN.md
- **S2**: S2_DECISION_DOSSIER.md
- **S3**: S3_ARCH_PROOF_HOOKS.md
- **S4**: S4_TRUTH_PACK_INDEX.json
- **S5**: S5_DECISION_GRAPH.json
- **S6**: S6_LEANTIME_ANALYSIS.md

**Hard Dependencies:** R (mandatory); soft X/T/Z (optional)
**Soft Dependencies:** X, T, Z, manual_rulings (optional)

**Notes:**
- Writes S_PHASE_TRUTH_PACK_PROVENANCE.json manifest documenting input sources and SHA-256 hashes
- Tracks missing expected inputs (X, T, Z artifacts) as optional
- Can skip steps via cfg.selected_s_steps
- Supports both legacy and registry-based prompt loading

---

## Core Execution Functions

### `_run_phase_inner()` — Line 11727
**Signature:**
```python
def _run_phase_inner(
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    collector: Optional[Collector],
    targets: Optional[List[str]],
    precollected_items: Optional[List[Dict[str, Any]]] = None,
    ui: Optional[UI] = None,
    selected_step_ids: Optional[Sequence[str]] = None,
) -> None
```

**Key Logic:**
1. **Load Prompts:** `prompts = get_phase_prompts(phase)` (line 11740)
2. **Filter by Selected Steps:** If `selected_step_ids` provided, filter prompts (lines 11741-11766)
3. **Validate Promptset:** Check `_prompt_hash_report_for_phase()` — if blocked, raises `PromptsetBlockedError`
4. **Collect/Verify Inputs:**
   - If `precollected_items` is provided: use directly (line 11783)
   - Else if `collector` is provided: call `collector.collect(subdirs=targets)` (line 11791)
   - Else: empty list (line 11788)
5. **Build Inventory:** `inventory = build_inventory(context_items, cfg.file_truncate_chars)` (line 11794)
6. **Build Partitions:** `partitions = build_partitions(phase, inventory, max_files=..., max_chars=...)` (lines 11796-11798)
7. **Write Inputs:** Write INVENTORY.json and PARTITIONS.json to `phase_dir/inputs/` (lines 11800-11815)
8. **Execute Steps:** For each prompt spec, execute step (not shown in excerpt, continues below)

**Auto-Partition Creation from Precollected:**
- `_run_phase_inner()` does NOT auto-create partitions — it always calls `build_partitions()`
- `build_partitions()` accepts the full inventory and creates partitions based on max_files and max_chars constraints
- Partitions are identified as `{phase}_P{0001,0002,...}` with file/char counts
- **The partitioning strategy is "artifact-aggregation"**: files are grouped into partitions by file/char limits, not by individual artifact types

---

### `collect_phase_artifacts()` — Line 13603
**Signature:**
```python
def collect_phase_artifacts(
    dirs: Dict[str, Path], phases: List[str], buckets: List[str]
) -> List[Dict[str, Any]]
```

**Used By:**
- **Phase Q** (line 14372): `collect_phase_artifacts(dirs, ["A", "H", "D", "C", "E", "W", "B", "G"], ["raw", "norm", "qa"])`
- **Phase Z** (line 15022): `collect_phase_artifacts(dirs, ["R", "X", "T"], ["raw", "norm", "qa"])`

**Behavior:**
- Iterates over `phases` list (e.g., ["A", "H", "D", "C"])
- For each phase, iterates over `buckets` list (e.g., ["raw", "norm", "qa"])
- Globs all *.json and *.md files from `dirs[phase] / bucket`
- Returns flattened list of items converted via `to_items(files)`

**Example:** Q phase collects all raw/norm/qa outputs from A through G for quality review.

---

### `get_phase_prompts()` — Line 4559
**Signature:**
```python
def get_phase_prompts(phase: str) -> List[PromptSpec]
```

**Behavior:**
- For Phase S: calls `_resolve_phase_s_prompts(get_active_s_prompts_mode())`
  - Can return "registry" or "legacy" sourced prompts
  - Registry prompts loaded from `phase_s_registry_path()` with tier_override
  - Fallback to legacy if registry unavailable
- For other phases: calls `_legacy_phase_prompt_specs(phase_code)`

**Prompt Loading (Legacy):**
- Globs `PROMPT_ROOT / PROMPT_{phase}*_*.md`
- Extracts step_id via regex: `r"PROMPT_([A-Z][0-9]+)_"`
- For each step, reads prompt file and calls `extract_output_artifacts(prompt_text, step_id)`
- Creates PromptSpec with step_id, prompt_path, output_artifacts, contract

**Output Artifacts Extraction:**
- Uses regex `OUTPUT_FILENAME_RE = r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b"`
- Searches for "# Outputs" / "## Outputs" / "# Goal(s)" sections
- Collects filenames matching pattern
- Falls back to `DEFAULT_OUTPUT_BY_STEP.get(step_id)` if not found in prompt
- Filters out invalid patterns (no underscores, .partX patterns)

---

## Partition Building Strategy

### `build_partitions()` — Line 5572
**Signature:**
```python
def build_partitions(
    phase: str, inventory: List[Dict[str, Any]], max_files: int, max_chars: int
) -> List[Dict[str, Any]]
```

**Algorithm:**
1. Iterate through inventory items (pre-sorted by path)
2. Accumulate items in `current_paths` until:
   - File count reaches `max_files`, OR
   - Estimated character count exceeds `max_chars`
3. Flush to partition with ID `{phase}_P{0001,0002,...}`
4. Each partition has: id, paths[], file_count, char_count_estimate
5. If no items collected, create empty partition `{phase}_P0001`

**Max Files Per Phase:**
```python
def max_files_for_phase(phase: str, cfg: RunnerConfig) -> int:
    if phase in CODE_HEAVY_PHASES:  # {"C", "E", "Q"}
        return cfg.max_files_code
    return cfg.max_files_docs
```

**Character Estimation:**
- Base chars from inventory item: `int(item.get("char_count_estimate", 0))`
- Add per-file overhead: `min(len(path) + 80, 2000)`
- Total est_chars = base + overhead

**Merge Step Pattern:**
The numbers "9" and "99" (e.g., A9, A99, H9, B9, etc.) represent:
- **X9**: Deterministic merge + QA step — consolidates X0-X8 raw outputs into norm outputs with QA report
- **X99**: Extended merge + QA (only in Phase A) — includes manifests and deep QA
- These are NOT separate from the main pipeline; they're defined as normal PromptSpecs with output_artifacts specifying the merged artifact names

**Normalization & Merging:**
The `normalize_step()` function (line 5765) handles:
1. Reads raw partition outputs: `{step_id}__{partition_id}.json`
2. Extracts artifacts: calls `extract_artifacts_from_partition_payload()`
3. **For .partX. artifacts:** writes individual partition files with numbered suffixes
4. **For merged artifacts:** calls `merge_json_chunks()` or `merge_markdown_chunks()`
5. Writes final norm output: `{artifact_name}` (without partition suffix)

---

## Summary Table: Hard & Soft Dependencies

| Phase | Hard Dependencies | Soft Dependencies | Input Method | Partition Strategy |
|-------|---|---|---|---|
| **A** | None | None | Collector scan | artifact-aggregation |
| **H** | None | None | Precollected (HOME_SAFE_ROOTS) | artifact-aggregation |
| **D** | None | None | Collector scan | artifact-aggregation |
| **C** | None | None | Collector scan | artifact-aggregation |
| **E** | None | None | Collector scan | artifact-aggregation |
| **W** | None | None | Collector scan | artifact-aggregation |
| **B** | None | None | Collector scan | artifact-aggregation |
| **G** | None | None | Collector scan | artifact-aggregation |
| **Q** | A, H, D, C, E, W, B, G | None | collect_phase_artifacts() | artifact-aggregation |
| **R** | A, H, D, C | None | Precollected (norm/) | artifact-aggregation |
| **X** | R | None | Precollected (norm/) | artifact-aggregation |
| **T** | R, X | None | Precollected (norm/) | artifact-aggregation |
| **Z** | R, X, T | None | collect_phase_artifacts() | artifact-aggregation |
| **S** | R | X, T, Z, manual_rulings | Precollected (norm/ + manual/) | artifact-aggregation |

---

## Comparison Lane (TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001)
**Location:** Lines 8696-8747

**Eligible Steps for Comparison Runs:**
```python
COMPARISON_ELIGIBLE_STEPS = frozenset({
    "A9", "H9", "B9", "G9", "R9", "S9", "T9", "W9", "X9",
})
```

**Purpose:** Compare outputs from alternative LLM providers/models alongside canonical lane

**Merge Step Participation:** All X9 steps participate (merge + QA eligible)

---

## Merge Artifacts Summary

The term "merge" refers to the consolidation phase (X9 steps, plus A99):

| Phase | Merge Step | Raw Inputs | Norm Outputs | QA Output |
|-------|---|---|---|---|
| **A** | A99 | A1-A13, A0 (inv) | A1-A8, A10-A13, A9 (all individ. + manifest) | REPOCTRL_NORM_MANIFEST.json, REPOCTRL_QA.json |
| **H** | H9 | H1-H7, H0 (inv) | H1-H7 (all individ. + manifest) | HOMECTRL_NORM_MANIFEST.json, HOMECTRL_QA.json |
| **D** | D4 | D1-D3, D0 (inv) | Merged D1-D3, D5 (topic clusters) | DOC_COVERAGE_REPORT.json |
| **C** | C9 | C1-C8, C10-C17, C0 (inv) | Merged C1-C17 (all) | CODE_SURFACES_QA.json |
| **E** | E9 | E1-E6, E0 (inv) | E1-E6 merged | EXEC_QA.json |
| **W** | W9 | W1-W5, W0 (inv) | W1-W5 merged | WORKFLOW_QA.json |
| **B** | B9 | B1-B3, B0 (inv) | B1-B3 merged | BOUNDARY_QA.json |
| **G** | G9 | G1-G4, G0 (inv) | G1-G4 merged | GOV_QA.json |
| **Q** | Q9 | All A-G outputs | Merged QA analysis | PIPELINE_DOCTOR_REPORT.json, QA_SERVICE_COVERAGE.json |
| **R** | (none) | A-C norm | R0-R10 (no merge step) | (implicit in synthesis) |
| **X** | X9 | X1-X4, X0 (inv) | X1-X4 merged | FEATURE_INDEX_QA.json |
| **T** | T9 | T0-T5, T0 (inv) | T0-T5 merged | TP_QA.json, TP_SUMMARY.md |
| **Z** | Z9 | R/X/T (all) | Checksums + manifest | FREEZE_QA.json |
| **S** | (none) | R, X?, T?, Z? | S0-S6 (no merge step) | (implicit in synthesis) |

