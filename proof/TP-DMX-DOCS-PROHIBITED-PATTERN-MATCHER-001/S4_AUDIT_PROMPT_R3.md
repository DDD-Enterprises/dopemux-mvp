You are an INDEPENDENT S4 auditor for a small CI-trust-policy repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family (Gemini)
from the implementer (Claude Sonnet). Verify independently by reading files and
running commands yourself in the current working directory (git worktree for
branch fix/docs-prohibited-pattern-matcher-001, already checked out).

## Packet under audit

TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001, round R3. PR #1225,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1225, base main, head
06abbf7119901bca1633728dd0ad12c9312857f6.

## Why R3 exists

R2 (commit 833f8cdac448dbf93f7d70e44526674fa48b37c7, already independently
audited PASS) fixed a policy-loosening gap in R1. Two automated Copilot review
findings on PR #1225 then flagged, against the R2 code:
1. scripts/ci/docs_prohibited_patterns.sh's header comment referenced a
   non-existent test path (tests/governance/test_docs_prohibited_patterns.py)
   instead of the real one (tests/ci/test_docs_prohibited_patterns.py).
2. tests/ci/test_docs_prohibited_patterns.py's
   test_mixed_batch_flags_only_the_forbidden_file asserted
   `"template-agent.md" not in result.stdout.split("temp.md")[0]` — only
   checking the stdout PREFIX before the first "temp.md" substring, so an
   allowed filename printed later in stdout would not fail the test (a weak
   assertion, not a real matcher bug).

R3 (commit 06abbf7119901bca1633728dd0ad12c9312857f6) claims to fix both,
with NO change to the actual matcher/policy logic.

## Required audit scope — verify each independently

1. **Diff scope and content.** Run
   `git diff 833f8cdac448dbf93f7d70e44526674fa48b37c7..HEAD --stat` and then
   the full diff for scripts/ci/docs_prohibited_patterns.sh and
   tests/ci/test_docs_prohibited_patterns.py. Confirm ONLY those two files
   changed, and confirm the change to docs_prohibited_patterns.sh is a
   COMMENT ONLY (no executable line changed) — i.e. the matcher logic
   (detemplated/is_prohibited/case statements) is byte-identical to R2.

2. **Comment fix is accurate.** Confirm the corrected path
   `tests/ci/test_docs_prohibited_patterns.py` mentioned in the script's
   header comment actually exists and is the real test file (it should be
   the same file you are reading right now).

3. **Test assertion fix is real and correct.** Read the updated
   `test_mixed_batch_flags_only_the_forbidden_file`. Confirm it now asserts
   `"template-agent.md" not in result.stdout` (full-stdout check, not a
   prefix slice) and `result.stdout.count("❌") == 1`. Run it directly:
   `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py::test_mixed_batch_flags_only_the_forbidden_file -v`
   and confirm it passes.

4. **No behavior change.** Independently execute the matcher against a
   representative sample from both R1 and R2's test matrices (at least 3
   allowed: template-agent.md, task-packet-template.md; at least 5 forbidden
   including the R2 anti-patterns: notes-template.md, todo-template.md,
   temp-template.md, scratch-template.md, temp.md) and confirm results are
   identical to what R2's audit already established (all still correct).

5. **Full suite.** Run
   `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py -v` — expect
   22 passed.

6. **Shell quality.** `bash -n` and `shellcheck` on
   scripts/ci/docs_prohibited_patterns.sh — both should be clean.

7. **Overall coherence.** Is this genuinely a no-op-for-policy hygiene fix
   (comment accuracy + test rigor) with zero change to what gets
   blocked/allowed? State your verdict plainly. If you find ANY behavioral
   difference versus R2, treat it as a blocking finding.

## Required output format

Produce a verdict: PASS or FAIL (or NEEDS_SUPERVISOR). List findings per
numbered scope item, noting what you executed vs. took on faith. Be
skeptical of the "comment/test only" claim — verify it by diffing, not by
trusting the commit message.
