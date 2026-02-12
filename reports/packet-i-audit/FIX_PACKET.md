# Packet I-AUDIT — FIX PACKET (ADVISORY — No FAIL)

## Summary
- Failures: **NONE** (overall PASS)
- Stop Conditions triggered: **NONE**
- This FIX_PACKET is ADVISORY — addresses drift items for completeness

---

## Advisory Fix 1: Remove or fix chronicle/tests/ (Drift Item 1)

### Root Cause
`chronicle/tests/test_*.py` files use `importlib.util.spec_from_file_location()` to dynamically import `store.py`, but `store.py` uses relative import `from .sqlite_migrations import ...` which requires a package context that `spec_from_file_location` doesn't provide.

### Recommended Fix: Delete redundant tests
The 4 tests in `chronicle/tests/` are fully superseded by `tests/unit/test_supersession_semantics.py` (which covers all 4 scenarios plus 11 more). Delete the redundant copies.

### Files to Change
- [ ] `services/working-memory-assistant/chronicle/tests/test_supersession_linearity.py` — DELETE
- [ ] `services/working-memory-assistant/chronicle/tests/test_supersession_depth_limit.py` — DELETE
- [ ] `services/working-memory-assistant/chronicle/tests/test_search_excludes_superseded_by_default.py` — DELETE
- [ ] `services/working-memory-assistant/chronicle/tests/test_retraction_tombstone.py` — DELETE
- [ ] `services/working-memory-assistant/chronicle/tests/__init__.py` — DELETE (empty dir)

### Verification
```bash
cd services/working-memory-assistant
PYTHONPATH=. python -m pytest -q tests/unit/ --ignore=tests/unit/test_copilot_adapter_hardening.py
# Should still pass 38 tests
```

---

## Advisory Fix 2: Update 07_mcp_contracts.md entry_type list (Drift Item 2)

### Root Cause
Documentation was not updated when `error`, `workflow_transition`, `task_event` were added to the schema CHECK constraint.

### Minimal Diff
```diff
--- a/docs/spec/dope-memory/v1/07_mcp_contracts.md
+++ b/docs/spec/dope-memory/v1/07_mcp_contracts.md
@@ -77,7 +77,7 @@
   "workspace_id": "string",
   "instance_id": "string",
   "session_id": "string|null",
-  "entry_type": "manual_note|decision|blocker|resolution|milestone",
+  "entry_type": "decision|blocker|resolution|milestone|error|workflow_transition|manual_note|task_event",
```

### Verification
```bash
rg "entry_type.*IN" services/working-memory-assistant/chronicle/schema.sql
# Compare with docs
```

---

## No Further Fixes Required

All Packet D through H semantics are correctly implemented in schema.sql (Path A canonical) and verified by 38 passing unit tests.
