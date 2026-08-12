# Independent auditor report — R2 — TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001 / PR #1225

- Runner: AGY / Google Antigravity CLI
- Model: `gemini-3.1-pro-high` (verified against the live `agy models` catalog)
- Independence: separate CLI process and model family from the implementer (Claude Sonnet, this session)
- Audited head: `833f8cdac448dbf93f7d70e44526674fa48b37c7` (branch `fix/docs-prohibited-pattern-matcher-001`, base `main`)
- Verdict: **PASS**

## Why R2 exists

An automated Codex review on PR #1225 (`chatgpt-codex-connector`) flagged that
R1's fix (commit `fcb7d2a95fbcdfdce3ac7e15a29c940791848c1a`, already
independently audited PASS) used a blanket
`case "$lbase" in *template*) continue ;; esac` that skipped **all**
prohibition checks for any filename containing "template" — not just the
temp-family ones. That meant a genuinely prohibited filename that also said
"template" (`todo-template.md`, `notes-template.md`, `temp-template.md`,
`scratch-template.md`) would incorrectly be allowed: a real regression
against the packet's own "no net loosening of the policy" invariant.

R2 (commit `833f8cdac448dbf93f7d70e44526674fa48b37c7`) fixes this by
stripping "template" occurrences only before the temp-family glob check
(`temp*.md`/`*temp*.md`), while `notes*.md`/`todo*.md`/`*scratch*.md` are
still checked against the untouched basename.

## Findings (verbatim verdict body from the auditor)

**VERDICT: PASS** — "R2 genuinely addresses the Codex-flagged gap without
reopening the original R1 false-positive or introducing major false
negatives. The logic is significantly sounder than R1."

1. **Codex finding is real** — verified by executing the R1 script directly:
   `docs/scratch/notes-template.md` incorrectly exited 0 under R1.
2. **R2 fixes it** — verified by executing R2 against all four flagged
   filenames (`todo-template.md`, `notes-template.md`, `temp-template.md`,
   `scratch-template.md`): all four now correctly exit 1 with `❌`.
3. **No regression on the R1 fix** — `template-agent.md` and
   `task-packet-template.md` still exit 0.
4. **No regression on the original deny-list** — spot-checked 8 forbidden
   filenames, all still correctly blocked.
5. **Adversarial probing** — the auditor tried its own edge cases beyond the
   test suite:
   - `docs/ttemplateemp.md`: stripping "template" concatenates the
     remainder into `temp.md`, so this gibberish filename is now blocked
     where R1 allowed it. Noted as a technical over-block, not a policy
     loosening, and "very unlikely to be used in production."
   - `docs/attempt.md`: blocked by `*temp*.md`, a pre-existing false
     positive inherited from before R1/R2, not introduced by this change.
   - `docs/templatemplate.md`: bash's `${var//pattern/}` non-overlapping
     match behaves correctly; not falsely blocked.
6. **Diff scope discipline** — verified via
   `git diff acffb54ba117b578277b7cd4361226ece8952609..HEAD --stat`: only
   `scripts/ci/docs_prohibited_patterns.sh` and
   `tests/ci/test_docs_prohibited_patterns.py` changed.
7. **Test suite** — 22/22 passed.
8. **Shell quality** — `bash -n` and `shellcheck` both clean.
9. **Full-tree safety** — `pre-commit run --all-files docs-prohibited-patterns`
   passed with no unexpected changes.
10. **Overall coherence** — PASS; "accurately implements the intended
    security constraints."

Raw auditor output is preserved verbatim at
`proof/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001/AGY_AUDIT_RAW_R2.txt`.

## Scope note

This audit covers `TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001` R2 / PR #1225
only. It does not touch, re-audit, or make any claim about PR #1224
(`TP-DMX-PR-PREP-SPECIALIST-V2-001`), which remains untouched.
