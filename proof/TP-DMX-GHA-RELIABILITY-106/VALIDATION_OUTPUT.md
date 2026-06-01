# TP-DMX-GHA-RELIABILITY-106 Validation Output

## Commands

| Command | Exit | Result |
|---|---:|---|
| `python -m json.tool task-packets/generated/TP-DMX-GHA-RELIABILITY-106.json >/tmp/tp106-json-tool.out` | 0 | PASS |
| `python -m json.tool proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json >/tmp/tp106-proof-json-tool.out` | 0 | PASS |
| `python -m jsonschema -i task-packets/generated/TP-DMX-GHA-RELIABILITY-106.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | 0 | PASS |
| `python - <<'PY' ... workflow trigger assertions ... PY` | 0 | PASS |
| `gh api repos/DDD-Enterprises/dopemux-mvp/branches/main/protection --jq '.required_status_checks.contexts \| index("📊 CI Pipeline Summary") != null'` | 0 | PASS (`true`) |
| `git diff --check` | 0 | PASS |
| `pre-commit run --files docs/ops/pr-gate-runbook.md docs/ops/branch-policy-audit.md docs/ops/ci-trigger-refresh.md task-packets/generated/TP-DMX-GHA-RELIABILITY-106.json proof/TP-DMX-GHA-RELIABILITY-106/AUDITOR_REPORT.md proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json proof/TP-DMX-GHA-RELIABILITY-106/VALIDATION_OUTPUT.md` | 0 | PASS |
| `python scripts/audit/validate_audit_proof.py proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json` | 1 | FAIL before adding required `embedded_audit` object |
| `python -m json.tool proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json >/tmp/tp106-proof-json-tool-2.out` | 0 | PASS |
| `python scripts/audit/validate_audit_proof.py proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json` | 0 | PASS |
| `pytest -q tests/ci/test_pr_gate.py` | 0 | PASS after gate-doc/test alignment |
| `python -m compileall -q tests/ci/test_pr_gate.py` | 0 | PASS after gate-doc/test alignment |
| `git diff --check` | 0 | PASS after proof shape fix |
| `pre-commit run --files docs/ops/pr-gate-runbook.md docs/ops/branch-policy-audit.md docs/ops/ci-trigger-refresh.md tests/ci/test_pr_gate.py task-packets/generated/TP-DMX-GHA-RELIABILITY-106.json proof/TP-DMX-GHA-RELIABILITY-106/AUDITOR_REPORT.md proof/TP-DMX-GHA-RELIABILITY-106/CHANGED_FILES.txt proof/TP-DMX-GHA-RELIABILITY-106/DIFF_STAT.txt proof/TP-DMX-GHA-RELIABILITY-106/GIT_STATE.md proof/TP-DMX-GHA-RELIABILITY-106/PROOF.json proof/TP-DMX-GHA-RELIABILITY-106/VALIDATION_OUTPUT.md` | 0 | PASS after proof shape fix |

## Notes

- The failing proof-validator run was expected after the first proof draft and
  triggered the embedded-audit proof shape fix.
- Final proof-validator rerun is recorded after the proof shape fix.
- Review repair aligned docs and structural tests to the current workflow gate:
  `audit-validator`, `extractor-full`, and `auditor-router` are blocking jobs.
