# Validation Output

## PASS

- `python -m json.tool task-packets/generated/TP-DMX-STEWARD-SCAFFOLD-302.json` exited 0.
- `python -m jsonschema -i task-packets/generated/TP-DMX-STEWARD-SCAFFOLD-302.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exited 0.
- `python -m compileall -q src tests` exited 0.
- `pytest -q tests/dopemux_init/test_pr_steward_scaffold.py` exited 0 with `2 passed`.
- `pytest -q tests/dopemux_init tests/test_project_init_templates.py` exited 0 with `8 passed`.
- `python -c "import yaml;yaml.safe_load(open('src/dopemux/templates/init/.github/workflows/pr-steward.yml'));yaml.safe_load(open('src/dopemux/templates/init/.github/workflows/embedded-audit.yml'));print('yaml ok')"` exited 0 with `yaml ok`.
- `pytest -q tests/dopemux_init` exited 0 with `2 passed`.
- `git diff --check` exited 0.
- `pre-commit run --files <TP302 implementation files>` exited 0.

## RED / Baseline

- `pytest -q tests/dopemux_init` exited 4 before the test directory existed on the TP301 base.
- `pytest -q tests/dopemux_init/test_pr_steward_scaffold.py` exited 1 after adding tests and before adding scaffold templates; the expected failure was missing `.github/workflows/pr-steward.yml`.

## NOT_RUN

- Live GitHub Actions execution of scaffolded workflows.
- Live downstream `dopemux init` run in a separate repository.
- External embedded audit invocation.
- Supervisor sign-off.
