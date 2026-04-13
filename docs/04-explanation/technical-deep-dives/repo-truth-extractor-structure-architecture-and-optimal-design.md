---
id: repo-truth-extractor-structure-architecture-and-optimal-design
title: 'Deep Analysis: Repo Truth Extractor (RTE) — Structure, Architecture & Optimal Design'
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-12'
last_review: '2026-04-12'
next_review: '2026-07-12'
prelude: Deep analysis of Repo Truth Extractor structure, current architecture, critical findings, optimal target design, and migration plan.
---
# Deep Analysis: Repo Truth Extractor (RTE) — Structure, Architecture & Optimal Design

## Part I: Current Architecture Map

### 1. System Overview

The Repo Truth Extractor (RTE) is a multi-phase, multi-provider LLM-powered codebase analysis engine that extracts structured truth from arbitrary repositories. It is the most complex subsystem in dopemux, spanning 55K+ lines of Python across 164 files, 138 promptset files, 82 test files, and 14 extraction phases.

### 2. Component Architecture (As-Is)

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      CLI / UX LAYER                                    │
│                                                                        │
│  dopemux audit wizard ──────── 8-stage interactive wizard              │
│  dopemux audit prescan ─────── corpus pre-scan (no LLM)               │
│  dopemux upgrades run ──────── v4 runner facade                        │
│  dopemux extract docs ──────── document entity extraction              │
│  dopemux extractor [LEGACY] ── redirects to upgrades                   │
│                                                                        │
│  src/dopemux/ux/wizard/  (11 files, ~1,700 LOC)                       │
│    runner.py → preflight → corpus → prompts → cost_profiles            │
│    → partitions → extraction → summary + display + stages              │
└─────────────┬──────────────────────────────────────────────────────────┘
              │ delegates via subprocess
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│               EXTRACTION ENGINE (services/repo-truth-extractor/)       │
│                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────────┐   │
│  │ run_v3.py   │  │ run_v4.py   │  │ run_v5.py [CANONICAL]        │   │
│  │ 12K lines   │  │ 1.1K lines  │  │ 20.7K lines                  │   │
│  │ LEGACY      │  │ BRIDGE      │  │ 13 classes, 368 functions    │   │
│  └─────────────┘  └─────────────┘  │ 442 exception handlers       │   │
│                                     │ 396 JSON parsing ops         │   │
│                                     └──────────────────────────────┘   │
│                                                                        │
│  14-Phase Pipeline: A → H → D → C → E → W → B → G → X → Q → R       │
│                     → T → Z → S                                        │
│                                                                        │
│  Post-Processing:  FL_INT (design claims)  │  S_INT (synthesis)        │
│  Comparison Lane:  Side-by-side model validation                       │
└─────────────┬──────────────────────────────────────────────────────────┘
              │ depends on
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    LIBRARY LAYER (lib/)                                 │
│                                                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐       │
│  │ prescan/         │  │ promptgen/       │  │ Core Modules     │       │
│  │ (19 files)       │  │ (19 files)       │  │                  │       │
│  │ engine.py        │  │ sync_engine.py   │  │ intelligence_    │       │
│  │ code_prescan.py  │  │ fingerprint.py   │  │  router.py (iR_l)│       │
│  │ grok_passes.py   │  │ feature_detector │  │ spend_ledger.py  │       │
│  │ classifier.py    │  │ contract_gen.py  │  │ batch_clients.py │       │
│  │ models.py        │  │ template_render  │  │ batch_retriever  │       │
│  └─────────────────┘  │ integrity_valid  │  │ struct_output_   │       │
│                        └─────────────────┘  │  contracts.py    │       │
│                                              └──────────────────┘       │
└─────────────┬──────────────────────────────────────────────────────────┘
              │ reads/writes
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    PROMPT ASSETS LAYER                                  │
│                                                                        │
│  promptsets/v4/ (138 files)       │  base_prompts/ (5 templates)       │
│    promptset.yaml (1076 lines)    │  prompts/v3/ (500+ files)          │
│    artifacts.yaml (2113 lines)    │  prompts/phase_fl_int/ (8 files)   │
│    model_map.yaml (3831 lines)    │  prompts/phase_s_int/ (5 files)    │
│    prompts/ (500+ step files)     │  prompts/phase_s/ (standalone)     │
└────────────────────────────────────────────────────────────────────────┘
```

### 3. Key Subsystems Deep Dive

#### 3.1 Intelligence Router (iR_l)

**What it is:** A prescan-to-extraction adapter that optimizes the extraction pipeline using pre-computed intelligence about the repository.

**Current implementation:** `lib/intelligence_router.py` — single class, ~80 lines

**API surface:**

- `should_skip(path)` → skip duplicate/noise files
- `should_skip_code(path)` → skip orphan code/test stubs
- `get_compression_hint(path)` → version chain summaries
- `get_phase_routing_override(path)` → reroute files to different phases
- `get_model_tier(path)` → premium/standard/economy model selection
- `get_bundling_group(path)` → partition co-location hints
- `reorder_partition(files)` → priority-based file ordering

**Problem:** iR_l is well-designed but minimally integrated. Only 2 unit tests exist. No integration tests prove that routing hints actually change extraction behavior.

#### 3.2 Prescan Pipeline

**Architecture:** 4-stage intelligence gathering → `prescan_intelligence.json`

- Corpus Walking — File inventory, size/type classification, authority labeling
- Code Intelligence — AST analysis, PageRank processing order, hotspot detection, orphan finding
- Duplicate Detection — Version chain identification, compression candidates
- Grok Passes (4 LLM-powered passes, optional):
  - DEDUP: Near-duplicate compression summaries
  - DISCOVER: Hidden feature/drift/ghost assessment
  - FEASIBILITY: Planned feature effort/risk analysis
  - OPTIMIZE: Routing hints, cost optimization, model tier suggestions

**Output artifacts:** 6 JSON files feeding iR_l and extraction phases

**Strength:** Well-architected, modular, optional, cost-tracked separately
**Gap:** Grok passes not well integrated with wizard UX; code intelligence stage partially wired

#### 3.3 Extraction Pipeline (v5)

**14-phase dependency graph:**

```text
Independent (parallel-safe):  A  H  D  C  E  W  B  G  X
Dependent:                    Q (requires all above)
                              R (requires A,H,D,C; optional B,E,G,W,Q,X)
                              T (requires R,X)
                              Z (requires R,X,T)
                              S (requires R; optional X,T,Z)
```

**Per-phase universal model:**

- X0: Inventory (mechanical indexing)
- X1-X2: Discovery (claims, boundaries)
- X3-X8: Synthesis (merge, normalize, QA)
- X9: Finalization (canonical merge)

**Contract enforcement:** Primary route → Repair route → Sidefill route per step

**Three routing policies:** cost / balanced / quality (8 named profiles)

#### 3.4 Promptgen System

**Pipeline:** fingerprint → archetype → feature_detect → phase_plan → interactive_discovery → scope_resolve → template_render → contract_gen → integrity_validate

**Key innovation:** Adaptive PromptPack V2 — 5 dynamic adjustment rules based on QA feedback from prior runs (split, shrink, reduce, strict, reorder)

**Contract trilogy:** `promptset.yaml` + `artifacts.yaml` + `model_map.yaml` — defines the complete extraction behavior

#### 3.5 Post-Processing

- FL_INT (Feature Ledger Intelligence): Design claims synthesis (F0→F4, L0→L4)
- S_INT (System Intelligence): MCP validation, hook mapping, contract coverage, gradecard, release plan (S16→S20)
- Comparison Lane: Run same prompts with different models, compare side-by-side without impacting canonical run

### 4. UX/UI Architecture

**Interactive Wizard (8 stages):**

- Stage 0: Welcome + system checks (Python, git, deps)
- Stage 1: Repo health (git status, branch, cleanliness)
- Stage 2: Corpus audit (prescan subprocess, authority classification)
- Stage 3: Prompt setup (promptset validation/generation)
- Stage 4: Cost profile (8 routing policies, cost estimation, API key check)
- Stage 5: Partition preview (file→phase mapping)
- Stage 6: Extraction (per-phase delegation with Run/Skip/Abort)
- Stage 7: Summary (telemetry, proof pack, next steps)

**Design patterns:**

- Rich terminal UI (tables, panels, progress bars, emojis)
- Two-mode execution (preview default, `--execute` for real)
- Educational panels (opt-in explanations)
- Phase-by-phase confirmation
- Subprocess delegation to `dopemux extract truth-run`

### 5. Dependencies & Integration

**CLI entry points (4 command groups):**

- `dopemux audit` — wizard + prescan + status [NEW, canonical]
- `dopemux upgrades` — v4 runner facade [NEW]
- `dopemux extract` — document/code extraction [ACTIVE]
- `dopemux extractor` — legacy, redirects to upgrades [DEPRECATED]

**External dependencies:** OpenRouter, OpenAI, Anthropic, xAI/Grok, Google Gemini, GitHub Models
**Internal dependencies:** LiteLLM proxy, Qdrant, PostgreSQL/AGE (optional), Redis (optional)

## Part II: Critical Findings

### 6. Architecture Pain Points

| # | Issue | Severity | Evidence |
| --- | --- | --- | --- |
| 1 | v5 monolith — 20.7K lines, 368 functions, 13 classes in ONE file | 🔴 CRITICAL | `run_extraction_v5.py` |
| 2 | Version duplication — v3 (12K) + v4 (1.1K) + v5 (20.7K) = 33.9K redundant lines | 🔴 CRITICAL | Three runner files |
| 3 | 82 tests excluded from CI — `pytest.ini` excludes `services/` | 🔴 CRITICAL | `pytest.ini`, `ci-complete.yml` |
| 4 | 84.5% functions undocumented — 311/368 functions lack docstrings | 🔴 CRITICAL | `run_extraction_v5.py` |
| 5 | iR_l under-integrated — Only 2 unit tests, no integration proof | ⚠️ HIGH | `tests/extractor/conftest.py` |
| 6 | Stringly-typed phases — No enum, string comparisons everywhere | ⚠️ HIGH | 16+ phase dispatcher functions |
| 7 | 442 scattered exception handlers — No centralized error strategy | ⚠️ HIGH | `run_extraction_v5.py` |
| 8 | Global state mutation — 20+ module-level constants mutated at runtime | ⚠️ MEDIUM | Module globals |
| 9 | Circular import risk — `lib/prescan/provider_catalog.py` imports v5 at runtime | ⚠️ MEDIUM | Line 33 |
| 10 | CLI command sprawl — 4 overlapping command groups (`audit`/`extract`/`extractor`/`upgrades`) | ⚠️ MEDIUM | CLI registration |

### 7. Strengths to Preserve

| # | Strength | Evidence |
| --- | --- | --- |
| 1 | Comprehensive 14-phase model — Well-thought dependency graph | Phase specs + v5 implementation |
| 2 | Contract trilogy — promptset/artifacts/model_map is a strong abstraction | `promptsets/v4/` |
| 3 | Prescan intelligence — Modular, optional, cost-tracked | `lib/prescan/` (19 files) |
| 4 | Adaptive PromptPack V2 — QA-driven feedback loop (5 rules) | `lib/promptgen/promptpack_v2.py` |
| 5 | Cost management — SpendLedger with per-phase, per-model tracking + hard limits | `lib/spend_ledger.py` |
| 6 | Comparison Lane — Validate without impact | `v5 --compare-mode` |
| 7 | Interactive wizard — 8-stage progressive disclosure UX | `src/dopemux/ux/wizard/` |
| 8 | Output safety — Secret redaction on all outputs | `output_safety.py` |
| 9 | 82 test files — Good coverage foundation | `services/repo-truth-extractor/tests/` |
| 10 | Feature detection — 99 built-in rules + interactive enrichment | `lib/promptgen/feature_detector.py` |

## Part III: Optimal Target Design

### 8. Proposed Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      CLI LAYER (unified)                               │
│                                                                        │
│  dopemux extract                                                       │
│    ├── prescan       # corpus intelligence audit                       │
│    ├── wizard        # interactive guided workflow                     │
│    ├── run           # direct phase execution                          │
│    ├── status        # run status/dashboard                            │
│    ├── validate      # pre-live gate + promptset integrity             │
│    └── compare       # comparison lane                                 │
│                                                                        │
│  (Retire: dopemux audit, dopemux extractor, dopemux upgrades)          │
└─────────────┬──────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER (NEW)                             │
│                                                                        │
│  extractor/                                                            │
│    orchestrator.py ──── Phase graph execution, dependency resolution   │
│    config.py ─────────── RunnerConfig + Phase enum + routing enums     │
│    cost_engine.py ────── Cost estimation, ledger integration           │
│    manifest.py ──────── Run manifest, proof pack, coverage rollup      │
│    resume.py ─────────── Resume state management                       │
│    comparison.py ────── Comparison lane orchestration                  │
└─────────────┬──────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  PHASE EXECUTION LAYER (NEW)                           │
│                                                                        │
│  extractor/phases/                                                     │
│    base.py ─────────── Abstract PhaseRunner + step dispatcher          │
│    repo_control.py ── Phase A: Repo Control Plane                      │
│    home_control.py ── Phase H: Home Control Plane                      │
│    docs.py ──────────── Phase D: Documentation Pipeline                │
│    code_surfaces.py ── Phase C: Code Surfaces                          │
│    execution.py ─────── Phase E: Execution Plane                       │
│    workflows.py ─────── Phase W: Workflow Plane                        │
│    boundaries.py ────── Phase B: Boundary Contracts                    │
│    governance.py ────── Phase G: Governance Plane                      │
│    features.py ──────── Phase X: Feature Index                         │
│    qa.py ─────────────── Phase Q: Quality Assurance                    │
│    arbitration.py ──── Phase R: Arbitration                            │
│    tasks.py ──────────── Phase T: Task Packets                         │
│    handoff.py ────────── Phase Z: Handoff Freeze                       │
│    synthesis.py ─────── Phase S: System Truths                         │
└─────────────┬──────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│              LLM INTERFACE LAYER (NEW)                                 │
│                                                                        │
│  extractor/llm/                                                        │
│    client.py ──────── Unified LLM call interface (call_llm)            │
│    routing.py ─────── Provider selection, escalation ladder            │
│    batch.py ──────── Batch API management                              │
│    contracts.py ──── Structured output schema enforcement              │
│    retry.py ──────── Retry + escalation + cost-aware fallback          │
└─────────────┬──────────────────────────────────────────────────────────┘
              │
              ▼
┌────────────────────────────────────────────────────────────────────────┐
│           INTELLIGENCE LAYER (prescan + iR_l + promptgen)              │
│           (Mostly preserved, minor refactoring)                        │
│                                                                        │
│  lib/prescan/    ─── Keep as-is (well-architected)                     │
│  lib/promptgen/  ─── Keep as-is (mature pipeline)                      │
│  lib/intelligence_router.py ─── Enhance integration                    │
│  lib/spend_ledger.py ────────── Keep as-is                             │
└────────────────────────────────────────────────────────────────────────┘
```

### 9. Key Design Decisions

| Decision | Rationale |
| --- | --- |
| Decompose v5 into ~15 phase modules | 20.7K monolith → ~1.5K per phase file; testable, reviewable, ownable |
| Introduce Phase enum | Replace all string comparisons; compile-time validation; IDE support |
| Create LLM interface layer | Extract `call_llm()`, retry logic, batch management; single responsibility |
| Unify CLI under `dopemux extract` | 4 overlapping groups → 1 coherent group; progressive disclosure preserved |
| Preserve `lib/prescan` & `lib/promptgen` | Already well-structured; don't fix what works |
| Enhance iR_l integration | Wire routing hints into orchestrator; add integration tests |
| Enable RTE tests in CI | 82 test files running = instant regression safety net |
| Retire v3 and v4 | Remove 13K lines of duplication; v5 is canonical |

## Part IV: Migration Plan (Current Reality → Optimal Design)

### Phase 0: Foundation & Safety Net (Week 1-2)

- Enable RTE tests in CI — Add `services/repo-truth-extractor/tests/` to CI pipeline (new workflow job or `pytest` config adjustment)
- Run full test suite manually — Identify failures, environment deps, API key requirements
- Document all 14 phase runner functions — Add docstrings to the 16 `run_phase_*()` functions in v5
- Create Phase enum — `extractor/config.py` with `Phase`, `RoutingPolicy`, `LaneClass` enums
- Add integration test for iR_l → extraction — Prove routing hints actually change extraction behavior

### Phase 1: Extract LLM Interface (Week 3-4)

- Extract `call_llm()` and retry logic — Move from v5 into `extractor/llm/client.py`
- Extract batch management — Move `batch_watch`, `batch_submit` into `extractor/llm/batch.py`
- Extract routing ladder — Move escalation logic into `extractor/llm/routing.py`
- Extract structured output contracts — Consolidate with `lib/structured_output_contracts.py`
- Create unified LLM test suite — Unit tests for `call_llm`, retry, escalation, batch

### Phase 2: Decompose Phase Runners (Week 5-8)

- Create PhaseRunner base class — Abstract interface: `configure()`, `execute()`, `validate_outputs()`, `get_dependencies()`
- Extract Phase A (Repo Control Plane) as first reference implementation
- Extract Phases H, D, C — Primary phases (most tested)
- Extract Phases E, W, B, G — Secondary phases
- Extract Phases X, Q, R, T, Z, S — Dependent/meta phases
- Wire phases into orchestrator — Phase graph resolution, dependency checking, parallel-safe execution

### Phase 3: Orchestration Layer (Week 7-9)

- Create Orchestrator class — Replaces v5's `main()` (388 lines)
- Extract config management — `RunnerConfig` into `extractor/config.py` with validation
- Extract manifest/proof — Run manifest, proof pack, coverage rollup into `extractor/manifest.py`
- Extract resume logic — Resume state management into `extractor/resume.py`
- Extract comparison lane — Into `extractor/comparison.py`
- Wire iR_l into orchestrator — Apply routing hints at partition/phase/model selection points

### Phase 4: CLI Unification (Week 9-10)

- Create unified `dopemux extract` command group — `prescan`, `wizard`, `run`, `status`, `validate`, `compare`
- Deprecate `dopemux audit` — Redirect to `dopemux extract wizard`/`prescan`
- Deprecate `dopemux extractor` — Already marked legacy
- Deprecate `dopemux upgrades` — Merge into `dopemux extract run`
- Update wizard — Point Stage 6 at new orchestrator API instead of subprocess

### Phase 5: Cleanup & Retirement (Week 10-12)

- Retire `run_extraction_v3.py` — Remove 12K lines; redirect any remaining references
- Retire `run_extraction_v4.py` — Remove 1.1K lines
- Retire deprecated code in v5 — Remove legacy prompt mode, deprecated iR_l parameter
- Remove dead imports and globals — 20+ module-level constants → config
- Update documentation — ADR for migration decision; update all reference docs; update README
- Full regression test — Run all 82 tests + wizard smoke test + extraction dry-run

### Phase 6: Enhancement (Post-Migration, Week 12+)

- Add Pydantic models — Replace 396 manual `json.loads()` with validated schemas
- Add async LLM calls — Replace synchronous `call_llm` with `async`/`await`
- Add dependency injection — Remove global state; enable isolated testing
- Add centralized error hierarchy — Replace 442 scattered exception handlers
- Add cross-phase artifact validation tests — Phase A output → Phase R input compatibility
- Wire code intelligence into wizard — Fully integrate `prescan_stages.py` into `WizardRunner`
- Add observability — OpenTelemetry spans for phase execution, LLM calls, cost tracking

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Breaking extraction during refactor | HIGH | CRITICAL | Enable CI tests first (Phase 0); extract one phase at a time; preserve v5 as fallback |
| Prompt regression | MEDIUM | HIGH | Contract trilogy (`promptset`/`artifacts`/`model_map`) stays unchanged; tests validate output schemas |
| Cost model divergence | LOW | MEDIUM | SpendLedger preserved as-is; cost tests cover pricing edge cases |
| Wizard UX disruption | LOW | MEDIUM | Wizard delegates via subprocess — can point at old or new orchestrator |
| iR_l integration regression | LOW | LOW | Add integration tests before wiring changes |
| Version upgrade stall | MEDIUM | MEDIUM | Clear deprecation schedule; v3/v4 retained until v5 extraction passes all tests |

### Success Criteria

- No file > 2,000 lines in the extraction engine
- All 82 tests passing in CI on every PR
- Single CLI entry point (`dopemux extract`) with 6 subcommands
- Phase enum eliminates all string-typed phase routing
- v3 and v4 retired — 13K lines removed
- iR_l integration tested — Routing hints provably change extraction behavior
- Function documentation > 80% — Up from 15.5%
- Zero deprecated code in active paths
