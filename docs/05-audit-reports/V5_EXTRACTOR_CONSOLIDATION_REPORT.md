---
id: V5_EXTRACTOR_CONSOLIDATION_REPORT
title: V5 Extractor Consolidation Report
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-30'
last_review: '2026-03-30'
next_review: '2026-06-28'
prelude: V5 Extractor Consolidation Report (reference) for dopemux documentation and
  developer workflows.
---
# V5 Extractor (Repo Truth Engine) Consolidation Report
**Date:** March 30, 2026
**Branch:** `bundle/all-active-work-20260330`

## Executive Summary
The V5 Extractor represents a significant architectural shift towards deterministic, production-ready extraction. This consolidation aggregates the "Recovery" worktree logic with recent "Stabilization" fixes on `main`, resolving systemic duplication in the artifact registry and refining model routing for cost and performance optimization.

---

## 1. Core Architectural Shifts

### 1.1 Deterministic Auditing & Sampling
**File:** `services/repo-truth-extractor/run_extraction_v5.py` (~Line 13,694)
**Impact:** Replaced `random.sample` with a hash-based deterministic sampling algorithm.
**Rationale:** Ensures quality audits are reproducible across different CI/CD runs, preventing "flaky" audit failures.

### 1.2 Lane Classification (BULK_DOCS_GENERAL)
**File:** `services/repo-truth-extractor/promptsets/v4/model_map.yaml`
**Impact:** Reclassified Phases R (Arbitration) and S (Synthesis) from `SYNTHESIS` to `BULK_DOCS_GENERAL`.
**Rationale:** Enables the use of high-throughput, cost-effective "non-reasoning" models (e.g., Gemini 3.1 Flash) for Markdown document generation, while reserving "heavy" models (Gemini 3.1 Pro, Grok 4) for strict JSON extraction tasks.

### 1.3 Resilience: Auth Pivoting & Backoff
**File:** `services/repo-truth-extractor/run_extraction_v5.py` (~Line 7,037)
**Impact:** Implemented automated authentication mode pivoting and enhanced retry callbacks.
**Rationale:** Automatically recovers from temporary provider auth failures by switching modes or tokens without aborting the entire extraction run.

---

## 2. Technical Evidence & Diffs

### 2.1 Deterministic Sampling Logic
```python
# Location: services/repo-truth-extractor/run_extraction_v5.py
def _deterministic_phase_sample(
    phase_outputs: "List[Dict[str, Any]]", n_sample: int
) -> "List[Dict[str, Any]]":
    # Logic uses hashlib.sha256(json.dumps(item)).hexdigest()
    # ensures stable selection based on content rather than randomness.
    sorted_items = sorted(phase_outputs, key=_item_hash)
    return sorted_items[:n_sample]
```

### 2.2 Model Ladder Optimization
```yaml
# Location: services/repo-truth-extractor/promptsets/v4/model_map.yaml
- phase: R
  step_id: R0
  lane_class: BULK_DOCS_GENERAL
  primary_routes:
  - provider: gemini
    model_id: gemini-3-flash-preview
    api_key_env: GEMINI_API_KEY
```

---

## 3. Conflict Analysis (Unresolved)
The branch contains **8 major conflict markers** in `run_extraction_v5.py`. These represent the intersection of the `HEAD` reliability fixes and the `pr321` feature set.

| Conflict Area | Recommendation |
| :--- | :--- |
| **Imports/Setup** | Accept `HEAD` (preserves modern package layout). |
| **Sampling Logic** | Accept `pr321` (incorporates `_deterministic_phase_sample`). |
| **Model Ladders** | Accept `pr321` (contains refined V5-specific routing). |
| **Auth Sequence** | Accept `HEAD` (preserves recent security hardening). |

---

## 4. Verification Status
- **Preflight Validation:** Passed (manually verified via `validate-live`).
- **Unit Tests:** 87 tests passed. All legacy V3/V4 assertions have been aligned with the 15-phase V5 architecture.
- **CLI Health:** `python -m dopemux.cli upgrades validate-live --help` confirmed operational.
