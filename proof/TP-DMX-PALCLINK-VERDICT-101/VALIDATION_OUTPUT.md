# Validation Output

PASS: python -m json.tool task-packets/generated/TP-DMX-PALCLINK-VERDICT-101.json
PASS: python -m compileall -q scripts/audit/pal_clink_runner.py tools/auditor_router/pal_clink.py tests/audit/test_pal_clink_runner.py tests/auditor_router/test_pal_clink.py
PASS: pytest -q tests/audit/test_pal_clink_runner.py (38 passed)
PASS: pytest -q tests/auditor_router/test_pal_clink.py (46 passed)
PASS: git diff --check

FAIL (pre-existing outside packet allowlist): python -m compileall -q tools scripts tests
- scripts/migration/switchover.py: SyntaxError at line 21
- scripts/partition_function.py: IndentationError at line 1
- scripts/submit_loop_context.py: IndentationError at line 1

NOT_RUN: live external PAL clink CLI invocation. Fixture run only; see PAL_CLINK_AUDIT_OUTPUT.json and AUDITOR_OUTPUT.json.
PASS: review repair marks fixture-only embedded audit as NEEDS_SUPERVISOR so it cannot satisfy passing audit gates.
