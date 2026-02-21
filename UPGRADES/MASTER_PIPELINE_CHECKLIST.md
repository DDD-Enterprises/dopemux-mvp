# Master Pipeline Checklist & Operational Guide

## 0. Setup & Initialization
- [ ] **Run Init**: `make x-run-init RUN_ID=<YYYYMMDD_HHMM_slug>`
- [ ] **Manifest**: Verify `extraction/latest/MANIFEST.json` is created with run metadata.
- [ ] **Stop Condition**: Fail if MANIFEST missing or run dir creation failed.

## 1. Phase A: Repo Control Plane
**Model**: Scanner (Gemini Flash 3 preferred)
**Inputs**: Repo root (excluding .git), focus on config/scripts/docs.
**Expected Outputs**:
- [ ] `REPO_CONTROL_INVENTORY.json`
- [ ] `REPO_INSTRUCTION_SURFACE.json`
- [ ] `REPO_ROUTER_SURFACE.json`
- [ ] `REPO_COMPOSE_SERVICE_GRAPH.json`
- [ ] `REPO_CI_GATES.json`
**Validation**:
- [ ] Run `make x-phase-normalize PHASE=A`
- [ ] Check `A_COVERAGE_REPORT.json` in `qa/` directory.

## 2. Phase H: Home Control Plane
**Model**: Scanner (Gemini Flash 3 preferred)
**Inputs**: `~/.dopemux`, `~/.config/dopemux`, `~/.config/taskx`, etc.
**Expected Outputs**:
- [ ] `HOME_INVENTORY.json`
- [ ] `HOME_KEYS_SURFACE.json` (Keys ONLY, no secrets)
- [ ] `HOME_MCP_SURFACE.json`
- [ ] `HOME_SQLITE_SCHEMA.json` (Schema only)
**Validation**:
- [ ] Run `make x-phase-normalize PHASE=H`
- [ ] Check `H_COVERAGE_REPORT.json`.
- [ ] **Security Check**: Fail if secrets detected.

## 3. Phase D: Docs Pipeline
**Model**: Scanner (Gemini Flash 3)
**Inputs**: `docs/**`
**Expected Outputs**:
- [ ] `DOC_INVENTORY.json`
- [ ] `DOC_CONTRACT_CLAIMS.json`
- [ ] `DOC_TOPIC_CLUSTERS.json`
- [ ] `DOC_CITATION_GRAPH.json`
**Validation**:
- [ ] Run `make x-phase-normalize PHASE=D`
- [ ] Check `D_COVERAGE_REPORT.json`.

## 4. Phase C: Code Surfaces
**Model**: Code Scanner (Grok-code-fast-1 preferred)
**Inputs**: `src/`, `services/`, `shared/`, `tools/`
**Expected Outputs**:
- [ ] `CODE_STRUCTURE_MAP.json`
- [ ] `SERVICE_ENTRYPOINTS.json`
- [ ] `EVENTBUS_SURFACE.json`
- [ ] `DOPE_MEMORY_SURFACES.json`
- [ ] `TRINITY_ENFORCEMENT_SURFACE.json`
- [ ] `RISK_LOCATIONS.json` (Determinism/Idempotency/Concurrency)
**Validation**:
- [ ] Run `make x-phase-normalize PHASE=C`
- [ ] Check `C_COVERAGE_REPORT.json`.

## 5. Phase E: Execution Plane
**Model**: Scanner (Gemini Flash 3)
**Inputs**: `scripts/`, `Makefile`, `compose/`
**Expected Outputs**:
- [ ] `EXEC_INVENTORY.json`
- [ ] `EXEC_COMMAND_INDEX.json`
- [ ] `EXEC_SERVICE_START_GRAPH.json`
**Validation**:
- [ ] Check `EXEC_COVERAGE_QA.json`.

## 6. Phase W: Workflow Plane
**Model**: Scanner (Gemini Flash 3)
**Inputs**: Docs + Code + Execution artifacts
**Expected Outputs**:
- [ ] `WORKFLOW_SOURCE_INDEX.json`
- [ ] `WORKFLOWS_EXTRACTED.json`
**Validation**:
- [ ] Check `WORKFLOW_QA.json`.

## 7. Phase B: Boundary Plane
**Model**: Scanner (Gemini Flash 3)
**Inputs**: Code + Docs + Intruction surfaces
**Expected Outputs**:
- [ ] `BOUNDARY_SOURCE_INDEX.json`
- [ ] `BOUNDARY_SURFACE.json`
- [ ] `BOUNDARY_BYPASS_CANDIDATES.json`
**Validation**:
- [ ] Check `BOUNDARY_QA.json`.

## 8. Phase G: Governance Plane
**Model**: Scanner (Gemini Flash 3)
**Inputs**: CI/Gates/Policy docs
**Expected Outputs**:
- [ ] `GOVERNANCE_SOURCE_INDEX.json`
- [ ] `GOVERNANCE_RULES.json`
**Validation**:
- [ ] Check `GOVERNANCE_QA.json`.

## 9. Phase Q: Pipeline Doctor
**Model**: Scanner (Gemini Flash 3)
**Inputs**: All previous artifacts
**Procedure**:
- [ ] Run `make x-doctor`
- [ ] Verify `PIPELINE_DOCTOR_REPORT.json` = PASS
- [ ] Verify `DOC_RECENCY_DUPLICATE_REPORT.json`

## 10. Phase R: Arbitration (Court)
**Model**: Reasoning (GPT-5.2 Extended)
**Inputs**: Normalized Artifacts from A/H/D/C/E/W/B/G/Q
**Expected Outputs**:
- [ ] `R_TRUTH_LEDGER.md`
- [ ] `R_CONFLICT_LEDGER.md`
- [ ] `R_BOUNDARY_MAP.md`
- [ ] `R_INVARIANTS_AND_ACCEPTANCE_TESTS.md`

## 11. Phase X: Feature Index & Catalogs
**Model**: Reasoning (GPT-5.2 Extended)
**Inputs**: R outputs + Artifacts
**Expected Outputs**:
- [ ] `X_SERVICE_CATALOG.json`
- [ ] `X_FEATURE_WORKFLOWS.json`

## 12. Phase T: Task Packets
**Model**: Reasoning (GPT-5.2 Extended)
**Inputs**: R Backlog + X Catalogs
**Expected Outputs**:
- [ ] `TP_INDEX.json`
- [ ] `TP_*.md` (Top N packets)

## 13. Phase Z: Handoff & Freeze
**Model**: Reasoning (GPT-5.2 Extended)
**Inputs**: Full pipeline state
**Expected Outputs**:
- [ ] `HANDOFF_BUNDLE.md`
- [ ] `HANDOFF_BUNDLE.json`

## Manual Steps (Post-Automation)
- **Phase R2 (Synthesis)**: Run manually via Opus / Claude Code.
  - Inputs: R outputs + full context.
  - Outputs: `R2_ARCHITECTURE_MODEL.md`, `R2_DECISION_LOG.md`.
