# Validation Output

## RED

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider tests/pr_merge_specialist/test_remediation_gate.py
exit_code=1

AttributeError: module 'dopemux_pr_merge_specialist.queue_drain' has no attribute 'require_steward_remediation_gate'
AttributeError: module 'dopemux_pr_merge_specialist.queue_drain' has no attribute 'global_fix_prs_allowed'
```

## PASS

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider tests/pr_merge_specialist/test_remediation_gate.py
exit_code=0
4 passed
```

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider tests/pr_merge_specialist/test_remediation_gate.py tests/pr_merge_specialist/test_agentic_thread_remediation.py tests/pr_merge_specialist/test_queue_drain_integration.py
exit_code=0
```

```text
PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider tests/pr_merge_specialist
exit_code=0
```

```text
python -m py_compile src/dopemux_pr_merge_specialist/queue_drain.py src/dopemux_pr_merge_specialist/policy.py tests/pr_merge_specialist/test_remediation_gate.py
exit_code=0
```

```text
python -m compileall -q src tests
exit_code=0
```

```text
python -m json.tool task-packets/generated/TP-DMX-MERGE-REMEDIATION-202.json
exit_code=0
```

```text
python -m jsonschema -i task-packets/generated/TP-DMX-MERGE-REMEDIATION-202.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit_code=0
```

```text
git diff --check
exit_code=0
```

```text
pre-commit run --files config/pr_merge_specialist/policy.yaml docs/ops/steward-merge-gate.md src/dopemux_pr_merge_specialist/queue_drain.py task-packets/generated/TP-DMX-MERGE-REMEDIATION-202.json tests/pr_merge_specialist/test_remediation_gate.py proof/TP-DMX-MERGE-REMEDIATION-202/AUDITOR_REPORT.md proof/TP-DMX-MERGE-REMEDIATION-202/CHANGED_FILES.txt proof/TP-DMX-MERGE-REMEDIATION-202/DIFF_STAT.txt proof/TP-DMX-MERGE-REMEDIATION-202/GIT_STATE.md proof/TP-DMX-MERGE-REMEDIATION-202/PROOF.json proof/TP-DMX-MERGE-REMEDIATION-202/VALIDATION_OUTPUT.md proof/TP-DMX-MERGE-REMEDIATION-202/review_bundle/README.md
exit_code=0
```

## NOT_RUN

```text
Task Orchestrator get_context
status=NOT_RUN
reason=Transport closed
```

```text
External embedded auditor
status=SKIPPED
reason=No supported external embedded-auditor invocation was available in this Codex session.
```
