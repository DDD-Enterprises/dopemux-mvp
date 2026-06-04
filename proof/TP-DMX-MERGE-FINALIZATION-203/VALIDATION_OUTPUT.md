# TP-DMX-MERGE-FINALIZATION-203 Validation Output

Generated: 2026-05-31T23:05:58Z

## RED

```text
$ pytest -q tests/pr_merge_specialist/test_finalization_gate.py
FFFFFF [100%]

Failures confirmed:
- queue_drain.require_steward_finalization_gate missing.
- run_merge_with_fallback still returned old rebase reason_code.
- missing expectedHeadOid did not block.
- governed auto-merge default did not return governed_automerge_disabled.
- approval-missing path still selected admin_bypass_squash.
```

```text
$ pytest -q tests/pr_merge_specialist/test_finalization_gate.py::test_graphql_expected_head_merge_does_not_use_pr_command_repo_flag
F [100%]

Failure confirmed gh api graphql command included --repo before fix.
```

## PASS

```text
$ python -m json.tool task-packets/generated/TP-DMX-MERGE-FINALIZATION-203.json
exit_code=0
```

```text
$ python -m jsonschema -i task-packets/generated/TP-DMX-MERGE-FINALIZATION-203.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit_code=0
```

```text
$ python -m compileall -q src tests templates/skills/pr-merge-specialist/scripts
exit_code=0
```

```text
$ pytest -q tests/pr_merge_specialist
........................................................................ [ 81%]
................                                                         [100%]
exit_code=0
```

```text
$ git diff --check
exit_code=0
```

```text
$ pre-commit run --files <TP203 changed files>
Validate YAML frontmatter in docs..........................................................Passed
Validate documentation against knowledge graph schema......................................Passed
Block prohibited documentation patterns (NOTES, TODO, TEMP, etc.)..........................Passed
Validate prelude <=100 tokens for efficient embeddings.....................................Passed
Enforce markdown file locations for changed files..........................................Passed
Enforce docs placement hygiene (changed files).............................................Passed
Enforce docs filename hygiene (kebab-case).................................................Passed
Audit docs filename hygiene (kebab-case, full-tree legacy debt)............................Passed
Reject executable/config code under UPGRADES (docs-only legacy tree)...(no files to check)Skipped
Enforce repository root hygiene (no random root files).....................................Passed
markdownlint...............................................................................Passed
trim trailing whitespace...................................................................Passed
fix end of files...........................................................................Passed
check yaml.................................................................................Passed
exit_code=0
```

## NOT_RUN

- Live GraphQL `mergePullRequest` execution: NOT_RUN. This packet implements and tests command construction/fail-closed behavior only; live merge authority remains supervisor-gated.
- External embedded audit: NOT_RUN locally. Proof records local bounded manual audit and expects independent PR CI/review.
- Supervisor sign-off: NOT_RUN. Required before live use of finalization authority.
