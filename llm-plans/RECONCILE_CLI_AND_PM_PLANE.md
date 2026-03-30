# Plan: Reconcile CLI and PM Plane Logic

## Objective
Reconcile the core application logic on the `bundle/all-active-work-20260330` branch, specifically bridging the new Interactive Flight Deck (TUI) with the Read-Only Series contract support in the PM plane.

## Strategic Approach
We will adopt a "Functional Future + Structural Stability" strategy:
1.  **Functional Future:** Adopt the `engine`-based abstractions and full adapter implementations from the feature branch (`wt-collect-dopemux-pr321`).
2.  **Structural Stability:** Port back the hardened error handling, CLI validation, and Dashboard UI improvements from `HEAD` (origin/main).

---

## Phase 1: PM Adapter Layer (`src/dopemux/pm/`)

### 1.1 Orchestrator Adapter
- **File:** `src/dopemux/pm/adapters/orchestrator.py`
- **Action:** Accept `wt-collect-dopemux-pr321` implementation.
- **Why:** Replaces `HEAD`'s "fail-closed" stubs with actual `/api/projects/{id}/workflow/context` and `/sprint/snapshot` read logic required for series navigation.

### 1.2 ConPort Adapter
- **File:** `src/dopemux/pm/adapters/conport.py`
- **Action:** Accept `wt-collect-dopemux-pr321` implementation.
- **Why:** Migrates from legacy `/kg/decisions/search` to the newer, more flexible `/api/decisions` endpoint structure.

---

## Phase 2: PR Merge Specialist CLI (`src/dopemux_pr_merge_specialist/`)

### 2.1 Engine-Based Initialization
- **File:** `src/dopemux_pr_merge_specialist/cli.py`
- **Action:** Adopt the `from . import engine` layout.
- **Task:** Port the `ORDERING_PLAN.json` loading logic and `build_run_paths` utility from `HEAD` into the new `cmd_flight` function.

### 2.2 Dashboard Reconciliation
- **File:** `src/dopemux_pr_merge_specialist/dashboard.py`
- **Action:** Ensure the `DopemuxDashboard.run()` signature supports the `ordering_plan` parameter from `HEAD`.

---

## Phase 3: Global CLI & Command Groups

### 3.1 Command Registration
- **File:** `src/dopemux/cli.py`
- **Action:** Manually unify the registration of `upgrades`, `extractor`, and `pr-merge` groups.
- **Task:** Ensure `pr-merge` correctly maps to the `dopemux_pr_merge_specialist.cli` entry point.

---

## Phase 4: Data Cleanup
- Discard current `extraction/` conflict markers.
- Run `git checkout --ours extraction/ docs/` to clear remaining noise.
- Regenerate extraction data using the stable, merged V5 runner.

---

## Verification Plan
1.  **Self-Check:** `PYTHONPATH=src python -m dopemux_pr_merge_specialist.cli self-check --smoke`
2.  **Unit Tests:** `PYTHONPATH=src pytest tests/unit/test_pm_adapter.py`
3.  **Manual TUI Check:** Launch `dopemux pr-merge flight` and verify project context loading.
