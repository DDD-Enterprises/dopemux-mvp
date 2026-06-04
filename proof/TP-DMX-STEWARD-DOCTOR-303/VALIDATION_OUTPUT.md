# Validation Output

## PASS

- `pytest -q tests/dopemux_cli/test_doctor.py` exited 0 with `5 passed`.
- `pytest -q tests/dopemux_cli/test_doctor.py tests/dopemux_cli/test_pr_steward_cmd.py` exited 0 with `10 passed`.
- `python -m pip install -e .` exited 0 and refreshed the editable install to this TP303 worktree.
- `python -m dopemux.cli pr-steward doctor --help` exited 0 and listed `--workspace`, `--schema`, and `--format`.
- `python -m json.tool task-packets/generated/TP-DMX-STEWARD-DOCTOR-303.json` exited 0.
- `python -m jsonschema -i task-packets/generated/TP-DMX-STEWARD-DOCTOR-303.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exited 0.
- `python -m json.tool schemas/pr_steward/config.schema.json` exited 0.
- `python -m compileall -q src tests` exited 0.
- `pytest -q tests/dopemux_cli` exited 0 with `10 passed`.
- `git diff --check` exited 0.
- `pre-commit run --files <TP303 changed files>` exited 0.

## RED

- `pytest -q tests/dopemux_cli/test_doctor.py` exited 1 before implementation; all five tests failed against placeholder doctor behavior.

## NOT_RUN

- Live downstream repository doctor execution.
- External embedded audit invocation.
- Supervisor sign-off.
