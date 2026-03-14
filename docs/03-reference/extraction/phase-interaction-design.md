---
title: "Phase Interaction Design"
id: phase-interaction-design
type: reference
status: active
date: "2026-03-14"
author: "copilot"
prelude: "How extraction phases feed into R (arbitration) and S (synthesis), model assignments, and dependency chains."
tags: [extraction, phases, arbitration, synthesis, model-routing]
---

# Phase Interaction Design

## Phase Ordering

The v5 extraction pipeline runs 14 phases in this order:

```
A → H → D → C → E → W → B → G → X → Q → R → T → Z → S
```

| Phase | Name | Category |
|-------|------|----------|
| **A** | Repo Control Plane | Independent extraction |
| **H** | Home Control Plane | Independent extraction |
| **D** | Docs Pipeline | Independent extraction |
| **C** | Code Surfaces | Independent extraction |
| **E** | Execution Plane | Independent extraction |
| **W** | Workflow Plane | Independent extraction |
| **B** | Boundary Plane | Independent extraction |
| **G** | Governance Plane | Independent extraction |
| **X** | Feature Index | Independent extraction (direct repo scan) |
| **Q** | Quality Assurance | Aggregator (validates A–G+X) |
| **R** | Arbitration | Evidence arbitration |
| **T** | Task Packets | Downstream (requires R+X) |
| **Z** | Handoff / Freeze | Downstream (requires R) |
| **S** | Synthesis | Final synthesis |

## Dependency Chain

```
Independent extraction:  A  H  D  C  E  W  B  G  X
                         │  │  │  │  │  │  │  │  │
Quality gate:            └──┴──┴──┴──┴──┴──┴──┴──┘→ Q
                                                     │
Arbitration:             A+H+D+C (required) ──→ R ← B+E+G+W+Q+X (optional)
                                                     │
Downstream:              R+X → T → Z
                         │         │
Synthesis:               R ────────┘──→ S (X/T/Z optional)
```

### R Phase Dependencies

| Dependency Type | Phases | Behavior |
|----------------|--------|----------|
| **Required** | A, H, D, C | R will not start without norm outputs from all four |
| **Optional** | B, E, G, W, Q, X | Collected when norm outputs exist; logged and skipped when absent |

### S Phase Dependencies

| Dependency Type | Phases | Behavior |
|----------------|--------|----------|
| **Required** | R | S will not start without R norm outputs |
| **Optional** | X, T, Z | Included when available; S still produces valid output without them |

## Optional Input Wiring: What B/E/G/W/Q/X Contribute to R

| Phase | Key Artifacts | R Steps Enriched | Evidence Gained |
|-------|--------------|------------------|-----------------|
| **B** (Boundary) | BOUNDARY_ENFORCEMENT_POINTS, REFUSAL_GUARDRAILS_SURFACE, BOUNDARY_BYPASS_RISKS | R3, R8, R10 | Guard chains, bypass vectors with severity, refusal rails |
| **E** (Execution) | EXEC_BOOTSTRAP_COMMANDS, EXEC_ENV_CHAIN, EXEC_STARTUP_GRAPH, EXEC_RUNTIME_MODES, EXEC_RISK_FACTS | R0, R5, R8 | Startup order, env precedence, service deps, runtime risk locations |
| **G** (Governance) | GOV_CI_GATES, GOV_POLICIES, GOV_SECRETS_SURFACE | R0, R6, R7 | Gate criteria, policy scope, enforcement tools, secret patterns |
| **W** (Workflow) | WORKFLOW_CATALOG, WORKFLOW_IO_MAP, WORKFLOW_COORDINATION_SURFACE, WORKFLOW_FAILURE_RECOVERY, WORKFLOW_STATE_COUPLING | R5, R6 | Runbook steps, service interactions, failure scenarios, state deps |
| **Q** (QA) | QA_MISSING_ARTIFACTS, QA_NORM_DRIFT_REPORT, PIPELINE_DOCTOR_REPORT | R7, R8 | Pipeline health, missing evidence gaps, drift between runs |
| **X** (Feature Index) | FEATURE_INDEX_MERGED, FEATURE_SURFACE, FEATURE_CODE_MAP, FEATURE_DEP_GRAPH | R0, R5, R8 | Feature-to-code mapping, dependency chains, coupling risks |

### R Step ↔ Optional Phase Mapping

| R Step | Name | Optional Inputs | What They Add |
|--------|------|----------------|---------------|
| R0 | Control Plane Truth Map | G, E, X | Governance authority, execution startup sequences, feature-to-code map |
| R3 | Trinity Boundary Enforcement | B | Boundary enforcement points, refusal rails |
| R5 | Workflows Truth Graph | W, E, X | Workflow catalog, execution graph, feature dependency chains |
| R6 | Portability Risk Ledger | G, W | Governance scope, state coupling |
| R7 | Conflict Ledger | Q, G | Pipeline health alerts, governance authority |
| R8 | Risk Register Top 20 | B, E, Q, X | Bypass risks, execution risks, evidence gaps, feature coupling |
| R10 | Two Plane Architecture | B, G | Boundary truth, governance enforcement |

### Why B/E/G/W/Q Do NOT Feed S

S synthesizes from R's arbitrated output. Once R has arbitrated evidence from the supplemental phases, the arbitration consensus captures it. S doesn't need the raw planes — it works from R truth maps. This prevents S from second-guessing R arbitration.

## Model Assignments

### Lane Classes

| Lane | Purpose | Primary Models |
|------|---------|----------------|
| **CE** | Strict schema enforcement, structured JSON output | gpt-5.3-codex, gpt-5.4 |
| **BULK_DOCS_GENERAL** | High-volume document processing | gemini-3-flash-preview, grok-non-reasoning |
| **SYNTHESIS** | Evidence arbitration and truth synthesis | grok-4.20-beta-reasoning, gemini-3.1-pro, gpt-5.3-codex |

### R/S Step Assignments

| Steps | Lane | Rationale |
|-------|------|-----------|
| R0, R2–R10 | SYNTHESIS | Evidence arbitration needs reasoning chains + large context |
| R1 | CE | Strict schema enforcement for structured arbitration output |
| S0–S11 | SYNTHESIS | Architecture synthesis needs strong reasoning models |
| S12 | CE | Strict schema enforcement for final validation |

### SYNTHESIS Lane Configuration

```yaml
lane_class: SYNTHESIS
strict_schema_required_primary: false
sidefill_enabled: true
repair_mode: targeted_then_envelope
primary_routes:
  - xai / grok-4.20-beta-0309-reasoning      # chain-of-thought arbitration
  - gemini / gemini-3.1-pro-preview           # large context synthesis
  - openrouter / openai/gpt-5.3-codex        # fallback
repair_routes:
  - openrouter / openai/gpt-5.4
sidefill_routes:
  - openrouter / openai/gpt-5.4
```

## Checking Phase Readiness

Use `--check-phases` to see per-phase status before running extraction:

```bash
dopemux extract truth-run --check-phases
dopemux extract truth-run --run-id FULL_RUN --check-phases
```

This shows:
- Per-phase status (complete / partial / raw only / failed / not started)
- Raw, norm, and failed artifact counts
- Dependency readiness for R and S phases
- Whether optional inputs are available

## Implementation Details

### Constants (run_extraction_v5.py)

```python
R_REQUIRED_INPUT_PHASES = ["A", "H", "D", "C"]
R_OPTIONAL_INPUT_PHASES = ["B", "E", "G", "W", "Q", "X"]
```

### Optional Collection Logic

In `run_phase_R()`, after collecting mandatory A/H/D/C norm files:

1. Iterate `R_OPTIONAL_INPUT_PHASES`
2. If phase has norm dir with `.json` or `.md` files → add to input, log INFO
3. If phase has empty norm dir or no norm dir → log INFO skip
4. Log summary of which optional phases contributed

### Prompt Contract Pattern

Each R prompt that accepts optional surfaces uses this pattern:

```markdown
HARD RULE: Reason from Phase A/H/D/C normalized artifacts (required).
If Phase X normalized artifacts are present in input, incorporate them
as supplemental evidence using the same citation discipline.

OPTIONAL SURFACES (use when present):
- Phase X: ARTIFACT_1, ARTIFACT_2 — description
```

## Phase Input Surfaces

Each independent phase scans specific repo directories. These targets are
expanded to cover all relevant input surfaces.

| Phase | Scan Targets |
|-------|-------------|
| **A** | 30+ root files and directories (comprehensive) |
| **H** | HOME_SAFE_ROOTS with safety filter (prescan) |
| **D** | `docs/` |
| **C** | `src, services, shared, plugins, tools, scripts, tests, docker/mcp-servers-source, docker/mcp-servers, components` |
| **E** | `scripts, tools, compose, .github, Makefile, package.json, docker, installers, install.sh, ops` |
| **W** | `docs, scripts, src, services, Makefile, compose.yml, docker, config` |
| **B** | `src, services, docs, contracts, config, .claude` |
| **G** | `.github, docs, .claude, AGENTS.md, pyproject.toml, .pre-commit-config.yaml, config/repo_hygiene, pytest.ini, Makefile, contracts` |
| **X** | `services, src, docs, config, scripts, Makefile, docker, compose.yml` (direct repo scan) |
| **Q** | Aggregates raw/norm/qa from A–G+X (meta-phase) |
| **T** | R/norm + X/norm + `AGENTS.md` + `.claude/PROJECT_INSTRUCTIONS.md` |

### Design Notes

- **Phase X** does a direct repo scan (not R artifacts) because X0–X4 prompt
  contracts expect to build a feature index from source code and config, not
  from arbitration outputs. X runs before Q and R so feature data flows into
  both quality checks and arbitration.
- **Phase T** includes governance context files (`AGENTS.md`,
  `.claude/PROJECT_INSTRUCTIONS.md`) because the T0 prompt contract requires
  repo governance constraints for task packet prioritisation.
