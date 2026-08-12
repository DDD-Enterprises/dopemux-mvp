You are an INDEPENDENT S4 auditor for a small CI-trust-policy repair packet in the
dopemux-mvp repository. You are running as a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Do NOT trust the implementer's framing
below — verify every claim independently by reading the actual repository files at
the current working directory (git worktree for branch
fix/docs-prohibited-pattern-matcher-001, already checked out) and by running commands
yourself where useful.

## Packet under audit

TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001, round R2 (a repair round on top of an
already-once-audited R1). PR #1225,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1225, base main, head
833f8cdac448dbf93f7d70e44526674fa48b37c7.

## Why R2 exists

R1 (commit fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a, already independently audited
PASS) fixed a false positive where docs-prohibited-patterns blocked legitimate
template-*.md filenames because *temp*.md substring-matched "temp" inside
"template". R1's fix used a blanket `case "$lbase" in *template*) continue ;; esac`
BEFORE the notes/todo/temp/scratch prohibition check — which an automated Codex
review on the PR (chatgpt-codex-connector) correctly flagged as a NEW policy hole:
that blanket continue skips ALL prohibition checks (not just the temp ones), so a
filename combining "template" with a genuinely prohibited token — e.g.
todo-template.md, notes-template.md, temp-template.md, scratch-template.md — would
now incorrectly be ALLOWED, which violates the packet's own explicit invariant that
"real temporary/scratch/notes/todo filenames must remain blocked (no net loosening
of the policy)".

R2 (this audit's target, commit 833f8cdac4) is the fix for that finding.

## Claimed R2 fix (verify, do not assume)

In scripts/ci/docs_prohibited_patterns.sh, instead of a blanket "if basename
contains template, skip all checks", the fix:
1. Computes `detemplated="${lbase//template/}"` (basename with all "template"
   occurrences removed).
2. Checks `notes*.md|todo*.md|*scratch*.md` against the ORIGINAL basename
   ($lbase) — unaffected by the template exemption.
3. Checks `temp*.md|*temp*.md` against the DE-TEMPLATED basename
   ($detemplated) only — so "temp" occurring solely as part of "template" no
   longer trips the temp-family patterns, but a real temp/scratch/notes/todo
   token elsewhere in the filename (including alongside "template") still does.
4. tests/ci/test_docs_prohibited_patterns.py gained 4 new FORBIDDEN_FILES cases:
   docs/scratch/todo-template.md, docs/scratch/notes-template.md,
   docs/scratch/temp-template.md, docs/scratch/scratch-template.md.

## Required audit scope — verify each independently

1. **Is the Codex finding real?** Read the R1 code (git show
   fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a:scripts/ci/docs_prohibited_patterns.sh
   or equivalent) and confirm that under R1's blanket `*template*) continue`, a
   file named e.g. `docs/scratch/notes-template.md` would in fact have been
   ALLOWED (a real policy-loosening bug), by tracing the logic or executing the
   R1 version yourself if convenient.

2. **Does R2 actually fix it?** Read scripts/ci/docs_prohibited_patterns.sh at
   the current (R2) head in full. Independently execute it against all four
   filenames from the Codex finding:
   `./scripts/ci/docs_prohibited_patterns.sh docs/scratch/todo-template.md`,
   `docs/scratch/notes-template.md`, `docs/scratch/temp-template.md`,
   `docs/scratch/scratch-template.md` — expect exit 1 / "❌" for all four.

3. **No regression on the original R1 fix.** Re-run the original allow-list:
   `./scripts/ci/docs_prohibited_patterns.sh docs/pr_prep/adapters/vibe/template-agent.md`
   and
   `./scripts/ci/docs_prohibited_patterns.sh docs/03-reference/governance/task-packet-template.md`
   — expect exit 0 / no "❌" for both (these must still be allowed).

4. **No regression on the original deny-list.** Spot check at least 3 of:
   temp.md, temp-foo.md, my-temp-file.md, temporary.md, notes.md, notes-foo.md,
   todo.md, scratch.md, foo-scratch-bar.md — all must still be exit 1 / "❌".

5. **Try to break it yourself.** The fix uses bash `${lbase//template/}`
   parameter substitution to strip ALL occurrences of the literal substring
   "template" before the temp-family check. Think of and test at least 2
   adversarial filenames of your own choosing that might expose an edge case
   in this approach (e.g. multiple "template" occurrences, "template" adjacent
   to "temp" in an unusual way, uppercase mixing before lowering, a filename
   where stripping "template" creates a NEW accidental temp*.md/*temp*.md
   match that shouldn't be there, etc.). Report what you tried and the result.

6. **Diff scope discipline.** Run
   `git diff acffb54ba117b578277b7cd4361226ece8952609..HEAD --stat` (or
   `..833f8cdac448dbf93f7d70e44526674fa48b37c7` if HEAD has moved) and confirm
   the ONLY files changed are scripts/ci/docs_prohibited_patterns.sh and
   tests/ci/test_docs_prohibited_patterns.py. No proof/, no packet JSON, no
   unrelated files.

7. **Test suite.** Run
   `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py -v` and confirm
   all tests (should be 22) pass, and that the 4 new test cases are meaningful
   (real assertions, not vacuous).

8. **Shell quality.** `bash -n scripts/ci/docs_prohibited_patterns.sh` and, if
   available, `shellcheck scripts/ci/docs_prohibited_patterns.sh` — both should
   be clean.

9. **Full-tree safety.** If feasible, run
   `pre-commit run --all-files docs-prohibited-patterns` and confirm no
   unexpected full-tree flag changes versus what you'd expect.

10. **Overall coherence.** Does R2 genuinely close the Codex-flagged gap without
    reopening the original R1 false-positive, and without introducing any new
    false-negative? State your verdict plainly.

## Required output format

Produce a verdict: PASS or FAIL (or NEEDS_SUPERVISOR if you cannot reach a
confident verdict). List findings per numbered scope item above, explicitly
noting what you actually executed/verified vs. what you are taking on faith.
Be skeptical — this is exactly the kind of change (a glob-matching bugfix
correcting a prior glob-matching bugfix) where a subtly wrong regex could look
right in the test suite but still be broken on an edge case, so actively try
to break it.
