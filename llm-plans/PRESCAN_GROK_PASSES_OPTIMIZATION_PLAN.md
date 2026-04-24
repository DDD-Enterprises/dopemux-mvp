# RTE Prescan: Grok Passes Optimization Plan

## Objective
Design and plan the optimal implementation of the LLM-driven "Grok Passes" (`dedup`, `discover`, `feasibility`, `optimize`) within the Repo Truth Extractor (RTE) prescan stage (Stage 0). Currently, these passes utilize placeholder one-liner prompts. This plan outlines the robust system prompts, context assembly logic, and testing strategies required to make these passes deterministic and highly effective for cost/scope optimization.

## Current State Analysis
The prescan stage successfully gathers deterministic non-LLM intelligence (SHA256 deduplication, version chain detection, Tree-Sitter parsing). This intelligence is fed into the `GrokPassRunner`. However, the prompts driving the LLM analysis are placeholders:
- `_DEDUP_SYSTEM_PROMPT = "You are a deduplication analyst."`
- `_DISCOVER_SYSTEM_PROMPT = "You are a technical archaeology analyst."`
- `_FEASIBILITY_SYSTEM_PROMPT = "You are a software feasibility analyst."`
- `_OPTIMIZE_SYSTEM_PROMPT = "You are an extraction cost optimizer."`

## 1. Optimal System Prompt Designs

To ensure strict compliance with the structured output schemas, the system prompts must be heavily engineered.

### 1.1 Dedup Pass
**Role**: Technical Redundancy Analyst
**Inputs**: `duplicate_groups` (from SHA256 hashes), `version_chains` (from filename patterns), file previews.
**Prompt Strategy**:
- **Directive**: Analyze the provided duplicate groups and version chains to definitively classify redundancy.
- **Rules**:
  - Differentiate between exact duplicates (can be skipped) and divergent forks (require deep extraction).
  - For version chains (e.g., `v1`, `v2`, `old`), write an `evolution_narrative` summarizing the architectural shift.
  - Emit `superseded_paths` explicitly for files that should not consume token budget in later phases.
- **Output Constraint**: Strict adherence to `schemas/dedup.json`.

### 1.2 Discover Pass
**Role**: Codebase Archaeology Expert
**Inputs**: `corpus_summary`, `symbols` (from Tree-Sitter), `ghost_files` (deleted/archived files), file previews.
**Prompt Strategy**:
- **Directive**: Identify undocumented capabilities, architectural drift, and valuable ghost files.
- **Rules**:
  - Map discovered features to the appropriate `extraction_phase` (e.g., A, H, D, C).
  - Compare declared intentions in root `README.md` against actual `api_surfaces` to detect `drift_signals`.
  - Assess `ghost_files` to determine if they contain logic `worth_restoring`.
- **Output Constraint**: Strict adherence to `schemas/discover.json`.

### 1.3 Feasibility Pass
**Role**: Implementation Risk Assessor
**Inputs**: `planned_features` (from user goals/PM plane), `dependency_clusters`, `api_surfaces`.
**Prompt Strategy**:
- **Directive**: Evaluate the structural feasibility of planned features against the current codebase architecture.
- **Rules**:
  - Assign a `foundation_score` (0.0 to 1.0) indicating how ready the codebase is for the feature.
  - Identify concrete `implementation_blockers` based on missing dependencies or conflicting API surfaces.
  - Flag `quick_win` opportunities if the foundation is already present.
- **Output Constraint**: Strict adherence to `schemas/feasibility.json`.

### 1.4 Optimize Pass (The Synthesis)
**Role**: Extraction Token Economics Optimizer
**Inputs**: Outputs from `dedup`, `discover`, and `feasibility`, plus `cost_estimates`.
**Prompt Strategy**:
- **Directive**: Synthesize prior intelligence into a rigid execution and routing plan to minimize token spend while maximizing truth extraction.
- **Rules**:
  - Populate `skip_list` strictly from confirmed `superseded_paths` (Dedup) and non-restorable ghost files (Discover).
  - Generate `compress_chains` rules dictating which files should only receive summary hints during extraction.
  - Apply `model_routing_hints`: Route high-complexity or high-PageRank paths to premium models; route boilerplate to economy models.
  - Apply `phase_routing_overrides`: Shift features discovered in unexpected places to their correct extraction phase.
- **Output Constraint**: Strict adherence to `schemas/optimize.json`.

## 2. Context Assembly Improvements (Payload Building)

The `_build_*_payload` methods in `services/repo-truth-extractor/lib/prescan/grok_passes.py` must be upgraded to provide maximum signal-to-noise:

1.  **Preview Truncation**: Strictly enforce `MAX_PREVIEW_BYTES` (6144) and `MAX_PREVIEW_LINES` (150) using a unified `_get_file_preview(entry)` helper to prevent context window overflow during prescan.
2.  **Dependency Graph Injection**: Feed PageRank scores and dependency clusters into the `optimize` and `feasibility` payloads.
3.  **Cross-Pass Provenance**: Ensure the `optimize` payload clearly maps insights back to the specific pass that generated them (e.g., tagging a skip recommendation as `source: dedup_pass`).

## 3. Broader Improvements and Extensions

### 3.1 Prescan Caching
- **Implementation**: Hash the `corpus_summary` and the raw file contents of the target partitions. Cache the Grok pass JSON outputs locally (`.dopetask/cache/prescan/`).
- **Benefit**: If an operator reruns `dopemux extract truth-run` without changing the source code, the expensive Grok passes bypass the LLM and load instantly.

### 3.2 Dynamic Batch Chunking
- **Current State**: Passes attempt to process the entire intelligence payload at once.
- **Improvement**: Implement a `TokenCounter` check before calling the LLM. If the `duplicate_groups` or `symbols` payload exceeds 80% of the model's context window, chunk the payload and run the pass in parallel batches, then merge the JSON responses.

### 3.3 Enhanced TUI Visibility
- **Extension**: Surface the `estimated_savings` (from the `optimize` pass) directly in the Dopemux TUI during the "Calibration" phase of the ritual.
- **UX**: Show the operator: `"Prescan complete. Saved 450K tokens (approx $2.25) by compressing 3 version chains and skipping 12 redundant files."`

## 4. Commit-Sized Execution Plan

| Slice | Description | Target Files |
|---|---|---|
| **Slice 1: Context Helpers** | Implement `_get_file_preview`, payload token counting, and caching logic in `GrokPassRunner`. | `lib/prescan/grok_passes.py`, `lib/prescan/incremental_cache.py` |
| **Slice 2: Dedup & Discover Prompts** | Inject engineered system prompts; wire specific Tree-Sitter & SHA256 context into their payload builders. | `lib/prescan/grok_passes.py` |
| **Slice 3: Feasibility & Optimize Prompts** | Inject engineered system prompts; wire dependency graph and prior pass results into their payloads. | `lib/prescan/grok_passes.py` |
| **Slice 4: Test Hardening** | Add unit tests mocking the grok responses to ensure the `BatchResponseValidator` and `IntelligenceRouter` correctly handle the new, richer schemas. | `tests/test_prescan_core_pipeline.py` |
| **Slice 5: TUI Integration** | Wire the `estimated_savings` output from the `optimize` pass to the `TaskSequencer` Calibration phase in the UI. | `src/dopemux/ui/dashboard.py`, `ui-dashboard/src/components/TaskSequencer.tsx` |

*Plan generated by Dopemux CLI / GPT-5.2-Pro.*