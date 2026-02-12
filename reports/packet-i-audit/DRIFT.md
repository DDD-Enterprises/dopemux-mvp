# Packet I-AUDIT — DRIFT REPORT

Date: 2026-02-12
Auditor: Claude Opus 4.6

---

## Summary

3 drift items found. **None are blocking or affect PASS/FAIL status.** All are test infrastructure or documentation lag issues.

---

## Drift Item 1: chronicle/tests/ import failure (4 tests unreachable)

- Area: tests
- Severity: **MEDIUM** (test coverage gap, not code defect)
- Expected: `chronicle/tests/test_*.py` should run via `pytest`
- Observed: All 4 tests fail during collection with `ImportError: attempted relative import with no known parent package`
- Evidence:
  - `chronicle/tests/test_supersession_linearity.py:8-14` uses `importlib.util.spec_from_file_location` to load `store.py`
  - `store.py:20` has `from .sqlite_migrations import apply_chronicle_migrations` (relative import)
  - Dynamic import via `spec_from_file_location` does not set `__package__`, so relative import fails
- Impact: 4 tests never run:
  - `test_supersession_linearity.py`
  - `test_supersession_depth_limit.py`
  - `test_search_excludes_superseded_by_default.py`
  - `test_retraction_tombstone.py`
- Mitigation: **All 4 scenarios ARE covered** by `tests/unit/test_supersession_semantics.py` which uses proper `PYTHONPATH=.` imports. No coverage gap in practice, but the duplicate tests create a false sense of additional coverage.
- Fix (minimal):
  ```
  Option A: Delete chronicle/tests/ (redundant with tests/unit/test_supersession_semantics.py)
  Option B: Fix imports to use absolute imports matching tests/unit/ pattern
  ```

---

## Drift Item 2: 07_mcp_contracts.md entry_type taxonomy lag

- Area: docs
- Severity: **LOW** (docs lag behind schema, no functional impact)
- Expected: docs should list all valid entry_type values
- Observed:
  - `07_mcp_contracts.md:79`: `"entry_type": "manual_note|decision|blocker|resolution|milestone"`
  - `schema.sql:43-45`: `CHECK (entry_type IN ('decision', 'blocker', 'resolution', 'milestone', 'error', 'workflow_transition', 'manual_note', 'task_event'))`
- Evidence:
  - docs/spec/dope-memory/v1/07_mcp_contracts.md:79
  - services/working-memory-assistant/chronicle/schema.sql:43-45
- Impact: Docs missing 3 entry_types: `error`, `workflow_transition`, `task_event`
- Fix (minimal): Update line 79 of 07_mcp_contracts.md to match schema.sql CHECK constraint

---

## Drift Item 3: chronicle/tests/ test for copilot adapter (unrelated import failure)

- Area: tests
- Severity: **LOW** (unrelated to Packet D-H audit, but noted)
- Expected: `tests/unit/test_copilot_adapter_hardening.py` should run
- Observed: Fails with `ModuleNotFoundError: No module named 'services.copilot_transcript_ingester'`
- Evidence: `tests/unit/test_copilot_adapter_hardening.py:3` imports copilot adapter which requires service not on PYTHONPATH
- Impact: One test in tests/unit/ doesn't run. Not relevant to Packet D-H semantics.
- Fix: Add `services/copilot_transcript_ingester` to PYTHONPATH or restructure import

---

## Known Good (No Drift)

The following areas were checked and found aligned:

1. **schema.sql vs migration end-state**: Fully aligned. schema.sql v1.2.1 contains all features from migrations v1.1.0 through v1.2.1.
2. **MCP contracts vs server implementation**: All 7 tools match docs for request/response shape and `success` field.
3. **Supersession scoping**: All 5 helper queries, DB index, and MCP tools consistently scope to (workspace_id, instance_id).
4. **Idempotency**: Docs declare optional key, implementation enforces when provided, test verifies.
5. **Time semantics**: ts_utc consistently set from source_event_ts_utc across store and MCP layer.
