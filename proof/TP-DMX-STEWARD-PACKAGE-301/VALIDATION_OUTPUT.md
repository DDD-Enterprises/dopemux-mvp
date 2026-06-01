# TP-DMX-STEWARD-PACKAGE-301 Validation Output

Generated: 2026-05-31T23:35:32Z

## RED

```text
$ pytest -q tests/dopemux_cli/test_pr_steward_cmd.py
ERROR tests/dopemux_cli/test_pr_steward_cmd.py
ModuleNotFoundError: No module named 'dopemux_pr_steward'
exit_code=2
```

```text
$ pytest -q tests/dopemux_cli/test_pr_steward_cmd.py::test_pr_steward_package_imports_outside_repo_root
FAILED
ModuleNotFoundError: No module named 'tools'
exit_code=1
```

## PASS

```text
$ python -m pip install -e .
Successfully installed dopemux-0.1.0
exit_code=0
```

```text
$ python -m json.tool task-packets/generated/TP-DMX-STEWARD-PACKAGE-301.json
exit_code=0
```

```text
$ python -m jsonschema -i task-packets/generated/TP-DMX-STEWARD-PACKAGE-301.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit_code=0
```

```text
$ python -m compileall -q src tests
exit_code=0
```

```text
$ pytest -q tests/dopemux_cli/test_pr_steward_cmd.py
.....                                                                    [100%]
exit_code=0
```

```text
$ pytest -q tests/dopemux_cli
.....                                                                    [100%]
exit_code=0
```

```text
$ pytest -q tests/dopemux_cli/test_pr_steward_cmd.py tests/test_cli.py
... [100%]
exit_code=0
```

```text
$ python -m dopemux.cli pr-steward --help
usage: dopemux-pr-steward [-h] [--contract-version] COMMAND ...
...
exit_code=0
```

```text
$ git diff --check
exit_code=0
```

```text
$ pre-commit run --files <TP301 changed files>
Validate YAML frontmatter in docs..........................................................Passed
Validate documentation against knowledge graph schema......................................Passed
Block prohibited documentation patterns (NOTES, TODO, TEMP, etc.)..........................Passed
Validate prelude <=100 tokens for efficient embeddings.....................................Passed
Enforce markdown file locations for changed files..........................................Passed
Enforce docs placement hygiene (changed files).............................................Passed
Enforce docs filename hygiene (kebab-case).................................................Passed
Audit docs filename hygiene (kebab-case, full-tree legacy debt)............................Passed
Enforce repository root hygiene (no random root files).....................................Passed
markdownlint...............................................................................Passed
trim trailing whitespace...................................................................Passed
fix end of files...........................................................................Passed
exit_code=0
```

## NOT_RUN

- Live GitHub PR Steward intake: NOT_RUN.
- Live Action Bridge compile against real PR artifacts: NOT_RUN.
- External embedded audit: NOT_RUN locally.
