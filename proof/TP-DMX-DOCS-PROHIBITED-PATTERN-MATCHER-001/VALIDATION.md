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

## Repair rounds (post-audit review findings)

Automated PR review (Codex, Copilot) on PR #1225 surfaced further findings
after R1's initial audit; each was independently re-audited (agy/
gemini-3.1-pro-high) before the embedded-audit gate would accept the
resulting head:

- **R2** (`833f8cdac448dbf93f7d70e44526674fa48b37c7`): Codex flagged that
  R1's blanket `*template*) continue` short-circuited *all* prohibition
  checks, not just the temp-family ones, so `todo-template.md` /
  `notes-template.md` / `temp-template.md` / `scratch-template.md` were
  incorrectly allowed — a real policy-loosening regression. Fixed by
  stripping `template` occurrences only before the temp-family glob check;
  `notes*.md`/`todo*.md`/`*scratch*.md` still run against the untouched
  basename. 4 regression tests added. Re-audited PASS (see
  `AUDITOR_REPAIR_REPORT.md`).
- **R3** (`06abbf7119901bca1633728dd0ad12c9312857f6`): Copilot flagged (a) a
  stale docstring path reference (`tests/governance/...` instead of the
  real `tests/ci/...`) and (b) a weak test assertion in
  `test_mixed_batch_flags_only_the_forbidden_file` that only checked the
  stdout prefix before the first match. Both fixed with zero change to the
  matcher's executable logic (independently confirmed byte-identical to
  R2). Re-audited PASS (see `AUDITOR_REPAIR_2_REPORT.md`).
- **R4** (packet-JSON only, no script/test change): Codex flagged that
  `task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json` failed
  `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` schema
  validation on two counts — the root-level `risk_lane` field is not a
  declared schema property (root `additionalProperties: false`), and
  `execution.agent: "claude"` is not in the schema's enum
  (`gemini`/`codex`/`vibe`/`shell`). Fixed by moving the L3 risk-lane
  designation into the `target` description text (matching this repo's
  existing convention — no other packet in `task-packets/` uses a
  `risk_lane` field) and changing `execution.agent` to `"shell"` (matching
  the convention used by other Claude-Code/shell-executed packets in this
  repo, e.g. `CCAR-001.json`). Also added the merge-proof directory
  (`proof/pr_merge/embedded-audit/pr-1225/**`, which Codex separately
  flagged as out-of-allowlist) to `commit.allowlist`. Verified with
  `Draft7Validator` against the canonical schema: 0 errors.

Every repair round required rebinding the signed embedded-audit proof to a
new `AUDIT_EVIDENCE_HEAD`, because `scripts/audit/local_audit_acceptance.py`
requires the delta from the audited commit to the enforced PR head to touch
*only* `proof/pr_merge/embedded-audit/pr-1225/**` — any further commit,
including a metadata-only packet-JSON fix, invalidates the prior proof's
binding by design. This is documented CI behavior (a prior Codex review
comment on this PR named the exact mechanism), not a defect.
