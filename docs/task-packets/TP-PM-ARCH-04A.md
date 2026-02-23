---
id: TP-PM-ARCH-04A
title: Tp Pm Arch 04A
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Tp Pm Arch 04A (explanation) for dopemux documentation and developer workflows.
---
# Task Packet: TP-PM-ARCH-04A · PM Plane · Canonical PMTask Model + Store (Unit-only)

════════════════════════════════════════════════════════════

## Objective

Implement a canonical PM task model and minimal store contract in `src/dopemux/pm/` with deterministic IDs, idempotent transitions, stale-write protection, and unit tests — no persistence backend, no event emission, no service wiring.

────────────────────────────────────────────────────────────

## Scope

IN:

* `PMTaskStatus` enum (canonical 5-value set)
* `PMTask` model (canonical lifecycle truth)
* `PMTransitionRequest` (with required `expected_version` + `idempotency_key`)
* `PMTaskStore` ABC + `InMemoryPMTaskStore` implementation
* Status dialect mapping tables (pure data, no runtime wiring)
* Unit tests under `tests/unit/pm/`

OUT:

* Persistent task store (SQLite/FS/ConPort/Leantime)
* EventBus integration
* Service integration (task-orchestrator/taskmaster)
* CLI commands
* ADHD overlays and cross-plane orchestration

────────────────────────────────────────────────────────────

## Invariants (Must Remain True)

* `task_id` is deterministic: `sha256(source:source_task_id)` when `source_task_id` exists, else `sha256(source:normalized(title):normalized(description))`. `created_at_utc` MUST NOT appear in hash inputs.
* `PMTaskStatus` has exactly 5 values: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELED`.
* Idempotency is per-transition: duplicate `(task_id, idempotency_key)` pairs are no-op replays returning prior result.
* Stale write protection: `expected_version != current.version` raises `StaleWriteError`.
* Trinity boundary: `dopemux.pm.*` imports nothing from Memory (ConPort), Search (Serena), or `services/*`.
* Existing `OrchestrationTask` in `services/task-orchestrator/task_orchestrator/models.py` is NOT modified.

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Plan (Numbered)

1. Create `src/dopemux/pm/` package with `__init__.py`
1. Implement `PMTaskStatus` enum, `PMTask` Pydantic model, `PMTransitionRequest`, and `content_hash_task_id()` in `models.py`
1. Implement `PMTaskStore` ABC, `TaskNotFoundError`, `StaleWriteError`, and `InMemoryPMTaskStore` in `store.py`
1. Implement status dialect mapping tables in `mapping.py`
1. Create `tests/unit/pm/` with `__init__.py`
1. Write `test_pm_models.py`: deterministic ID, normalization, field validation
1. Write `test_pm_store.py`: create idempotency, transition idempotency, stale write, version increment
1. Write `test_pm_mapping.py`: mapping table completeness, lossy mapping documentation

────────────────────────────────────────────────────────────

## Files to Touch

* `src/dopemux/pm/__init__.py` — NEW
* `src/dopemux/pm/models.py` — NEW
* `src/dopemux/pm/store.py` — NEW
* `src/dopemux/pm/mapping.py` — NEW
* `tests/unit/pm/__init__.py` — NEW
* `tests/unit/pm/test_pm_models.py` — NEW
* `tests/unit/pm/test_pm_store.py` — NEW
* `tests/unit/pm/test_pm_mapping.py` — NEW

If additional files are needed, stop and request approval.

────────────────────────────────────────────────────────────

## Exact Commands to Run

* `mkdir -p src/dopemux/pm tests/unit/pm`
* `python -m pytest tests/unit/pm/ --collect-only`
* `python -m pytest tests/unit/pm/ -v --tb=short`
* `python -m pytest tests/unit/ -v --tb=short --maxfail=3`
* `python -m pytest tests/unit --maxfail=1 --disable-warnings --no-cov`
* `python -c "from dopemux.pm.models import PMTask, PMTaskStatus; print('OK')"`
* `python -c "from dopemux.pm.store import InMemoryPMTaskStore; print('OK')"`
* `python -c "from dopemux.pm.mapping import ORCHESTRATOR_TO_CANONICAL; print('OK')"`

────────────────────────────────────────────────────────────

## Output Capture Rules (Verbatim)

Implementer must return:

* `git diff --stat`
* `git show --name-only --oneline HEAD`
* All command outputs verbatim
* Exit codes
* Import check outputs

────────────────────────────────────────────────────────────

## Acceptance Criteria

* `PMTaskStatus` has exactly 5 values: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELED`
* Deterministic task IDs: same `(source, source_task_id)` → same `task_id`; `created_at_utc` excluded
* Transition idempotency: same `(task_id, idempotency_key)` replay returns identical state (no version bump)
* Stale write refusal: `expected_version` mismatch raises `StaleWriteError`
* Trinity clean: no forbidden imports (`services/`, `event_bus`, `mcp`, ConPort, Serena)
* All required pytest commands pass with 0 failures

Each criterion should be testable.

────────────────────────────────────────────────────────────

## Rollback Steps

* `rm -rf src/dopemux/pm/`
* `rm -rf tests/unit/pm/`
* `git checkout -- .`

Keep rollback explicit.

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop immediately if:

* `git status --porcelain` is not empty before starting
* `src/dopemux/pm/` already exists
* Adding `src/dopemux/pm/` breaks existing package imports
* `pyproject.toml` pytest config has changed from evidence
* Any test in `tests/unit/` fails before our changes (baseline broken)
* Trinity boundary would be violated (need to import from services/event_bus/mcp)

If stopped, return:

* What you attempted
* Evidence collected
* What output is needed next

────────────────────────────────────────────────────────────

## Locked Decisions

* **ConPort Decision #1**: Task ID policy — `sha256(source:source_task_id)` primary, `sha256(source:norm_title:norm_desc)` fallback
* **ADR-PM-001**: Canonical task object (proposed)
* **ADR-PM-002**: PM event taxonomy (proposed)
* **ADR-PM-003**: Storage — derived/mirrored boundaries (proposed)

## Git Workflow

* Branch: `codex/pm-plane/arch-04a`
* Commit: `pm: add canonical pm task model + store (unit-tested)`
