---
id: EXTRACTION_V5_QUICK_REFERENCE
title: Extraction V5 Quick Reference
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Extraction V5 Quick Reference (explanation) for dopemux documentation and
  developer workflows.
---
# DopeMux Truth Extractor v5 - Quick Reference

## Phase Handler Functions & Line Numbers

| Phase | Handler Function | Line | Input Method | Output Artifacts |
|-------|---|---|---|---|
| **A** | `run_phase_A()` | 14158 | Collector (.claude, .dopemux, config, scripts, tools, compose, .github, docs, etc.) | A0-A13, A99: inventory, surfaces (instruction, MCP, router, hooks, compose, litellm, taskx, leantime, editor, CLI, hook-contract), behavior hints, event flow, manifests, QA |
| **H** | `run_phase_H()` | 14230 | Precollected (HOME_SAFE_ROOTS: .dopemux, .config/*) | H0-H9: inventory, keys, MCP, router/ladder, litellm, profiles, tmux, sqlite, manifests, QA |
| **D** | `run_phase_D()` | 14284 | Collector (docs/) | D0-D5: inventory, partitioned indexes/claims/boundaries/supersession/notices, citation graph, merged docs, topic clusters, duplicates, coverage |
| **C** | `run_phase_C()` | 14262 | Collector (src, services, shared, plugins, tools, scripts, tests) | C0-C17, C9: inventory, service entrypoints, eventbus, dope-memory, trinity, taskx, workflows, APIs, risks (determinism/idempotency/concurrency), catalogs, agents, QA |
| **E** | `run_phase_E()` | 14299 | Collector (scripts, tools, compose, .github, Makefile, package.json) | E0-E6, E9: inventory, bootstrap, env-chain, startup-graph, runtime-modes, artifacts, risks, merged, QA |
| **W** | `run_phase_W()` | 14318 | Collector (docs, scripts, src, services) | W0-W5, W9: inventory, catalog, I/O-map, coordination, failure-recovery, state-coupling, merged, QA |
| **B** | `run_phase_B()` | 14335 | Collector (src, services, docs) | B0-B3, B9: inventory, enforcement-points, guardrails, bypass-risks, merged, QA |
| **G** | `run_phase_G()` | 14352 | Collector (.github, docs, .claude, AGENTS.md) | G0-G4, G9: inventory, CI-gates, hygiene, policies, secrets, merged, QA |
| **Q** | `run_phase_Q()` | 14369 | collect_phase_artifacts(A-G, [raw,norm,qa]) | Q0-Q3, Q9: run-manifest, missing-artifacts, collisions, drift-report, doctor-report, coverage |
| **R** | `run_phase_R()` | 14900 | Precollected (A,H,D,C norm/) | R0-R10: control-plane, dope-memory, eventbus, trinity, taskx, workflows, portability, conflicts, risks, leantime, two-plane truths (markdown) |
| **X** | `run_phase_X()` | 14930 | Precollected (R norm/) | X0-X4, X9: inventory, feature-surface, code-map, doc-map, dep-graph, merged-index, QA |
| **T** | `run_phase_T()` | 14952 | Precollected (R,X norm/) | T0-T5, T9: instructions, packets (partitioned), schema, batched (partitioned), deduped, collisions, run-plan, merged, QA, summary |
| **Z** | `run_phase_Z()` | 15019 | collect_phase_artifacts(R,X,T, [raw,norm,qa]) | Z0-Z2, Z9: file-index, checksums, proof-pack, manifest, freeze-manifest, readme, QA |
| **S** | `run_phase_S()` | 14973 | Precollected (R norm/ + X,T,Z,manual) | S0-S6: architecture-synthesis, migration-plan, decision-dossier, proof-hooks, truth-pack-index, decision-graph, leantime-analysis |

## REQUIRED_PROMPT_STEP_IDS (All Steps per Phase)

```
A: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A99 (15)
H: H0, H1, H2, H3, H4, H5, H6, H7, H9 (9)
D: D0, D1, D2, D3, D4, D5 (6)
C: C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C14, C15, C16, C17 (18)
E: E0, E1, E2, E3, E4, E5, E6, E9 (8)
W: W0, W1, W2, W3, W4, W5, W9 (7)
B: B0, B1, B2, B3, B9 (5)
G: G0, G1, G2, G3, G4, G9 (6)
Q: Q0, Q1, Q2, Q3, Q9 (5)
R: R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10 (11)
X: X0, X1, X2, X3, X4, X9 (6)
T: T0, T1, T2, T3, T4, T5, T9 (7)
Z: Z0, Z1, Z2, Z9 (4)
S: S0, S1, S2, S3, S4, S5, S6 (7)
```

## R_REQUIRED_INPUT_PHASES & R_REQUIRED_ARTIFACT_GROUPS

### R_REQUIRED_INPUT_PHASES
```python
["A", "H", "D", "C"]
```

### R_REQUIRED_ARTIFACT_GROUPS (mandatory outputs from Phase R inputs)

**Phase A** - 10 groups:
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

**Phase H** - 7 groups:
- HOME_MCP_SURFACE.json, HOME_ROUTER_SURFACE.json, HOME_PROVIDER_LADDER_HINTS.json
- HOME_LITELLM_SURFACE.json, HOME_PROFILES_SURFACE.json, HOME_TMUX_WORKFLOW_SURFACE.json
- HOME_SQLITE_SCHEMA.json

**Phase D** - 5 groups:
- DOC_TOPIC_CLUSTERS.json, DOC_SUPERSESSION.json, DOC_CONTRACT_CLAIMS.json
- (DUPLICATE_DRIFT_REPORT.json OR DOC_RECENCY_DUPLICATE_REPORT.json)
- DOC_INDEX.json

**Phase C** - 13 groups:
- SERVICE_ENTRYPOINTS.json, EVENTBUS_SURFACE.json, EVENT_PRODUCERS.json, EVENT_CONSUMERS.json
- DOPE_MEMORY_CODE_SURFACE.json, DOPE_MEMORY_SCHEMAS.json, DOPE_MEMORY_DB_WRITES.json
- TRINITY_ENFORCEMENT_SURFACE.json, REFUSAL_AND_GUARDRAILS_SURFACE.json
- TASKX_INTEGRATION_SURFACE.json, WORKFLOW_RUNNER_SURFACE.json
- DETERMINISM_RISK_LOCATIONS.json, IDEMPOTENCY_RISK_LOCATIONS.json, CONCURRENCY_RISK_LOCATIONS.json

## Phase Dependencies

### Hard Dependencies (must have norm outputs before running)
- **R** ← A, H, D, C
- **X** ← R
- **T** ← R, X
- **Z** ← R, X, T
- **S** ← R (+ optional X, T, Z)
- **Q** ← A, H, D, C, E, W, B, G

### Soft Dependencies (optional, some steps may benefit from)
- **None** (all dependencies are hard requirements)

## Partition Building Strategy

### `build_partitions()` (Line 5572)
- **Method**: artifact-aggregation (files grouped by size, not by type)
- **Partitions Named**: `{phase}_P{0001,0002,...}`
- **Splitting Logic**:
  - max_files threshold (cfg.max_files_code for C/E/Q, else cfg.max_files_docs)
  - max_chars threshold (cfg.max_chars)
  - Per-file overhead: min(len(path) + 80, 2000) chars
- **Partition Contents**: paths[], file_count, char_count_estimate
- **Auto-Creation**: YES — `_run_phase_inner()` always calls `build_partitions()`

### Precollected Items Handling
- **Phases with Collector**: A, H, D, C, E, W, B, G (direct file scan → build_partitions)
- **Phases with Precollected**: H (collector.collect), Q (collect_phase_artifacts), R/X/T/Z/S (norm/ files)
- **All go through build_partitions()** — there's no special "precollected" partition type

## Input Collection Methods

| Method | Phases | How It Works |
|--------|--------|---|
| **Direct Collector** | A, D, C, E, W, B, G | Pass collector + targets to `_run_phase_inner()`, it calls collector.collect(subdirs=targets) |
| **Precollected via Collector.collect()** | H | Call collector.collect(subdirs=HOME_SAFE_ROOTS) before phase, pass items to `_run_phase_inner()` |
| **Precollected via collect_phase_artifacts()** | Q, Z | Glob *.json/*.md from specific phase buckets (raw/norm/qa) |
| **Precollected from norm/ dirs** | R, X, T, S | Glob *.json/*.md from phase norm/ directories |

## Merge Step Pattern (X9 & A99)

**What They Do:**
- Consolidate raw partition outputs → single normalized merged artifacts
- Extract & deduplicate items from partition raw files
- Sort deterministically (by path, id, etc.)
- Generate QA reports (missing artifacts, empty artifacts, field validation)

**Naming:**
- Step X9 merges steps X0-X8 outputs
- Step A99 is extended merge (also includes manifests, deeper QA than typical X9)
- Other phases have X9 (H9, D4, C9, E9, W9, B9, G9, Q9, X9, T9, Z9)

**Comparison Lane Eligible:** A9, H9, B9, G9, R9, S9, T9, W9, X9
- Can run against alternative LLM provider/model alongside canonical lane
- Results stored under raw/comparison/{provider}__{model}/

## Key Functions

### `_run_phase_inner()` (Line 11727)
```python
def _run_phase_inner(phase, dirs, cfg, collector, targets,
                     precollected_items=None, ui=None, selected_step_ids=None)
```
- **Does NOT auto-partition from precollected**: always calls `build_partitions()`
- **Validates prompts**: checks hash report, blocks if missing/unreadable
- **Writes inputs**: INVENTORY.json, PARTITIONS.json
- **Filters steps**: if selected_step_ids provided, filters prompts
- **Does not call build_partitions directly in view**: it's called at line 11796

### `collect_phase_artifacts()` (Line 13603)
```python
def collect_phase_artifacts(dirs, phases, buckets) -> List[Dict[str, Any]]
```
- **Globs**: `dirs[phase] / bucket / *.json` and `*.md`
- **Used by**: Q (8 prior phases), Z (3 prior phases)
- **Returns**: flattened list of items ready for build_partitions()

### `get_phase_prompts()` (Line 4559)
```python
def get_phase_prompts(phase: str) -> List[PromptSpec]
```
- **Phase S special**: calls `_resolve_phase_s_prompts(mode)` (registry or legacy)
- **Other phases**: `_legacy_phase_prompt_specs(phase)`
- **Output Extraction**: regex `[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)`
- **Each PromptSpec**: step_id, prompt_path, output_artifacts, tier_override, source, contract

## Step Tiers & Routing

```python
STEP_TIERS = ("bulk", "extract", "synthesis", "qa")
```

- **Inventory/Partitioning (X0)**: bulk tier
- **Extraction (X1-X8)**: extract tier (unless tier_override)
- **Merge/QA (X9)**: synthesis/qa tier (unless tier_override)
- **Routing Ladders**: cost/balanced/balanced_openrouter/balanced_grok_openrouter/quality

## Comparison Eligible Steps

```python
COMPARISON_ELIGIBLE_STEPS = {"A9", "H9", "B9", "G9", "R9", "S9", "T9", "W9", "X9"}
```

## HOME_SAFE_ROOTS Configuration

```python
HOME_SAFE_ROOTS = [
    ".dopemux", ".config/dopemux", ".config/taskx",
    ".config/litellm", ".config/mcp"
]
```

**Allowed Suffixes**: .yaml, .yml, .toml, .json, .md, .txt, .ini, .cfg, .conf

**Denied Globs**: *.db, `*`.sqlite*, `*`.log, `*`.cache, `*`.tmp, `*`.swp, `*`cache*, `*`logs*, `*`.pem, `*`.p12, `*`.pfx, `*`.der, `*`.crt, `*`key*, `*`token*, `*`secret*, `*`pass*, `*`credential*

## CODE_HEAVY_PHASES

```python
CODE_HEAVY_PHASES = {"C", "E", "Q"}
```

These phases use `cfg.max_files_code` (typically higher) instead of `cfg.max_files_docs` for partitioning.
