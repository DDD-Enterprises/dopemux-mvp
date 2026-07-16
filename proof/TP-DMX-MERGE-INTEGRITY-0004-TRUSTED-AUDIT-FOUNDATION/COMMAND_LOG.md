# Command log — TP-DMX-MERGE-INTEGRITY-0004 remediation (0001R2 Phase A)

| Command | Exit |
|---|---|
| `python -m pytest -q tests/audit/test_pr_audit_router.py tests/audit/test_run_embedded_audit.py tests/pr_steward/test_intake.py --no-cov` | 0 |
| `python -m compileall -q scripts/audit tools/pr_steward` | 0 |
| workflow YAML `yaml.safe_load` | 0 |
| `jsonschema.validate` task packet vs dopetask-canonical-spec | 0 |
| `pre-commit run --files <changed>` | 0 |
| `git diff --check` | 0 |
| PAL codereview (gemini-2.5-pro external) | API 429; internal workflow complete |
| PAL secaudit (gemini-2.5-pro external) | API 429; internal workflow complete |
