# TP-DMX-STEWARD-GATE-201 Validation Output

| Command | Exit | Result |
|---|---:|---|
| `pytest -q tests/pr_merge_specialist/test_steward_gate.py` before implementation | 2 | RED_PASS: missing `steward_gate` module |
| `pytest -q tests/pr_merge_specialist/test_steward_gate.py` after implementation | 0 | PASS: 5 tests passed |
| `python -m compileall -q src tests` | 1 | FAIL_ENV: no space left on device while writing `__pycache__` |
| `python -m json.tool task-packets/generated/TP-DMX-STEWARD-GATE-201.json` | 0 | PASS |
| `python -m jsonschema -i task-packets/generated/TP-DMX-STEWARD-GATE-201.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | 0 | PASS |
| `python -c "purity static check"` | 0 | PASS |
| `python -c "ast.parse changed Python files"` | 0 | PASS |
| `git diff --check` | 0 | PASS |
| `PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider tests/pr_merge_specialist/test_steward_gate.py` | 0 | PASS: 5 tests passed |
| `python scripts/audit/validate_audit_proof.py proof/TP-DMX-STEWARD-GATE-201/PROOF.json` | 0 | PASS |
| `pre-commit run --files <TP201 changed files>` | 0 | PASS |

The broad compile command failed for environment capacity, not a Python syntax
error. The filesystem reported roughly 100-400 MB free during this slice, and
pytest capture also failed until capture/cache were disabled.
