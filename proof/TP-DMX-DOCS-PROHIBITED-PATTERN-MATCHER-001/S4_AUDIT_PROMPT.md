You are an INDEPENDENT S4 auditor for a small CI-trust-policy repair packet in the
dopemux-mvp repository. You are running as a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Do NOT trust the implementer's framing
below — verify every claim independently by reading the actual repository files at
the current working directory (this is the git worktree for branch
fix/docs-prohibited-pattern-matcher-001, already checked out) and by running commands
yourself where useful.

## Packet under audit

TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001 (risk lane L3, because it touches
.pre-commit-config.yaml, CI trust policy). PR #1225,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1225, base main, head
fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a.

## Claimed problem

The docs-prohibited-patterns pre-commit hook flags changed docs/task-packets
markdown basenames against the glob
notes*.md|todo*.md|temp*.md|*temp*.md|*scratch*.md. *temp*.md substring-matches
"temp" anywhere in the filename, including inside "template" — so legitimate
template asset filenames (e.g. docs/pr_prep/adapters/vibe/template-agent.md) were
misclassified as prohibited temp files. Commit 139944337a on main renamed
agent-template.md to template-agent.md specifically to escape this hook, but the
glob was never fixed, so the false positive persists on main today.

## Claimed fix (verify, do not assume)

1. The inline bash matcher previously embedded in .pre-commit-config.yaml was
   extracted into scripts/ci/docs_prohibited_patterns.sh.
2. The classification logic was changed: any basename containing "template" is now
   treated as a template asset and skipped, before the temp/notes/todo/scratch
   prohibition check runs — replacing a prior one-off hardcoded exemption for a
   single exact path (task-packet-template.md only).
3. .pre-commit-config.yaml's docs-prohibited-patterns hook entry now calls the
   extracted script instead of inlining the bash.
4. New regression tests were added at tests/ci/test_docs_prohibited_patterns.py.

## Required audit scope — verify each independently

1. **Root cause verification**: Read git log/show for commit 139944337a on main
   (or its effect) and confirm the *temp*.md glob does in fact still match
   "template-agent.md" as claimed. Do not take this on faith — trace the actual
   glob logic.

2. **Diff scope discipline**: Run `git diff origin/main..HEAD --stat` and confirm
   the changed files are EXACTLY: .pre-commit-config.yaml,
   scripts/ci/docs_prohibited_patterns.sh, tests/ci/test_docs_prohibited_patterns.py,
   task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json, and
   proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/**. No other file should be
   touched. No PR #1224 content should be present on this branch.

3. **No policy loosening**: Read scripts/ci/docs_prohibited_patterns.sh in full.
   Confirm that a file whose basename does NOT contain "template" is still
   correctly rejected when it matches notes*.md, todo*.md, temp*.md, *temp*.md,
   or *scratch*.md. Confirm this by actually executing the script yourself against
   both allowed and forbidden sample filenames, e.g.:
   `./scripts/ci/docs_prohibited_patterns.sh docs/scratch/temp.md` (expect exit 1,
   "❌" in output) and
   `./scripts/ci/docs_prohibited_patterns.sh docs/pr_prep/adapters/vibe/template-agent.md`
   (expect exit 0). Try a few more of your own choosing (e.g. notes-foo.md,
   my-temp-file.md, a template-*.md variant not in the test file) to probe for
   edge cases the tests might have missed.

4. **No one-off exemption anti-pattern**: Confirm the fix is a general
   classification fix (any "*template*" basename), not a hardcoded exemption for
   one specific filename. This was an explicit operator requirement — flag it as a
   finding if you find a hardcoded single-path exemption instead of a general rule.

5. **Test suite correctness**: Read tests/ci/test_docs_prohibited_patterns.py and
   actually run it: `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py -v`.
   Confirm it passes and that the assertions are meaningful (not vacuous — e.g. not
   just checking "no exception raised" when a real check is needed).

6. **Hook wiring correctness**: Confirm .pre-commit-config.yaml's
   docs-prohibited-patterns hook actually invokes scripts/ci/docs_prohibited_patterns.sh
   (correct path, executable bit, `pass_filenames: true` preserved, `files`/`exclude`
   patterns unchanged from before). If pre-commit is installed, run
   `pre-commit run docs-prohibited-patterns --files docs/pr_prep/adapters/vibe/template-agent.md`
   yourself and confirm it passes.

7. **Full-tree safety**: If feasible, run
   `pre-commit run --all-files docs-prohibited-patterns` and confirm no unexpected
   full-tree file gets newly flagged or newly un-flagged versus what you'd expect.

8. **Shell quality**: Confirm scripts/ci/docs_prohibited_patterns.sh is syntactically
   valid bash (`bash -n`) and, if shellcheck is available, run it and report any
   findings.

9. **Task packet schema sanity**: Confirm
   task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json is valid JSON and its
   commit.allowlist matches the actual changed files.

10. **Overall coherence**: Does this genuinely fix the stated bug without
    introducing a new false-negative (a real temp/scratch/notes/todo file that
    would now slip through)? State your verdict plainly.

## Required output format

Produce a verdict: PASS or FAIL (or NEEDS_SUPERVISOR if you cannot reach a
confident verdict). List findings per numbered scope item above, explicitly noting
what you actually executed/verified vs. what you are taking on faith. Be skeptical —
this is exactly the kind of change (a glob-matching bugfix) where a subtly wrong
regex could look right in the test suite but still be broken on an edge case, so
actively try to break it.
