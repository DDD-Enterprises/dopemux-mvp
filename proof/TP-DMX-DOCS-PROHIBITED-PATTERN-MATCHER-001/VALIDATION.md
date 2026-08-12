# Validation — TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001

Base: `origin/main` @ `9dce8ffaec489f486d0356d300f0e8ea5aefa3d2`
Branch: `fix/docs-prohibited-pattern-matcher-001`
Worktree: `.worktrees/fix-docs-prohibited-pattern-matcher-001`

## Root cause

`.pre-commit-config.yaml`'s `docs-prohibited-patterns` hook matched changed
doc/task-packet basenames against the glob
`notes*.md|todo*.md|temp*.md|*temp*.md|*scratch*.md`. `*temp*.md`
substring-matches the token `temp` anywhere in the filename, including
inside `template`. Commit `139944337a` renamed
`docs/pr_prep/adapters/vibe/agent-template.md` to `template-agent.md`
specifically intending `template-*` filenames to stop tripping this hook,
but the glob was never updated, so the rename did not fix the false
positive — it is still misclassified as a prohibited temp file.

## Fix

- Extracted the inline bash matcher from `.pre-commit-config.yaml` into
  `scripts/ci/docs_prohibited_patterns.sh` (same logic, now independently
  testable and shellcheck-clean).
- Fixed the classification: any basename containing `template` is treated
  as a template asset and skipped before the temp/notes/todo/scratch
  prohibition check runs, instead of hardcoding a single exact-path
  exemption (`task-packet-template.md`) as the previous code did.
- `.pre-commit-config.yaml`'s hook `entry` now points at the script.

## Deterministic checks performed (PASS unless noted)

| Check | Result |
|---|---|
| `bash -n scripts/ci/docs_prohibited_patterns.sh` | PASS |
| `shellcheck scripts/ci/docs_prohibited_patterns.sh` | PASS (no findings) |
| `python3 -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"` | PASS |
| `python3 -c "import json; json.load(open('task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json'))"` | PASS |
| `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py -v` (18 cases) | PASS — see `PYTEST_OUTPUT.txt` |
| `./scripts/ci/docs_prohibited_patterns.sh docs/pr_prep/adapters/vibe/template-agent.md` | exit 0 (allowed) |
| `./scripts/ci/docs_prohibited_patterns.sh docs/scratch/temp.md` | exit 1 (blocked) |
| `pre-commit run docs-prohibited-patterns --files docs/pr_prep/adapters/vibe/template-agent.md` | Passed |
| `pre-commit run docs-prohibited-patterns --files docs/scratch/temp-check.md` (throwaway real-temp file, not committed) | Failed as expected (❌ Found prohibited file pattern) |
| `pre-commit run --all-files docs-prohibited-patterns` (full tree, base main) | Passed — no other repo file's classification changed |
| `git diff --check` | PASS (no whitespace errors) |

## Regression matrix (`tests/ci/test_docs_prohibited_patterns.py`)

**Allowed** (previously false-positive, now correctly pass):
`template-agent.md`, `template-task.md`, `template-canonical-pr.md`,
`task-packet-template.md`, `TEMPLATE-AGENT.md` (case-insensitivity).

**Still rejected** (no policy loosening):
`temp.md`, `temp-foo.md`, `my-temp-file.md`, `temporary.md`, `notes.md`,
`notes-foo.md`, `todo.md`, `scratch.md`, `foo-scratch-bar.md`,
`task-packets/temp-draft.md`.

Plus: mixed-batch isolation (one forbidden file among allowed ones is
still flagged), quarantined `docs/04-explanation/history/sourceFiles/`
paths are skipped, and non-docs/non-task-packets paths are ignored.

## Scope discipline

Touched only: `.pre-commit-config.yaml`, `scripts/ci/docs_prohibited_patterns.sh`,
`tests/ci/test_docs_prohibited_patterns.py`,
`task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json`, this
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/**` bundle. No other
hook, no PR #1224 content, no `template-agent.md` rename/delete.

## Independent audit

Per the L3 gate on this packet (`.pre-commit-config.yaml` is CI trust
policy): implementer is Claude Sonnet (this session). Independent audit by
a separate model/runtime family is required before merge. `merge=NOT_AUTHORIZED`
until that audit records a PASS verdict.
