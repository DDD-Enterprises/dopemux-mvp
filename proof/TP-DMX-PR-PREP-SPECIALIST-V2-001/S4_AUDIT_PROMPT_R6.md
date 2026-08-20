You are an INDEPENDENT L2 auditor for a docs-governance repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Verify independently by
reading files and running commands yourself in the current working
directory: /Users/hue/code/dopemux-mvp, branch
feat/pr-prep-specialist-v2-contract (already checked out).

## Packet under audi

TP-DMX-PR-PREP-SPECIALIST-V2-001, round R6. PR #1224,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1224, base main, head
ecab6aba71e204fc47337bee13b37e1b715dc37d.

## Why R6 exists

The prior R5 scoped-audit PASS was revoked by operator decision after
fresh repository truth exposed real defects: main had advanced 9 commits
past the R5 head; 4 live unresolved PR review threads reported broken
compatibility relative links; and the R3/R4 terminal semantic census
turned out to be a FALSE NEGATIVE -- it never searched for `TP-PRPS-000` or
`7-step`, so it missed that six adapter README families (claude, cursor,
gemini, jules, copilot, vibe) still actively declared a retired V1
contract (`Contract: TP-PRPS-000-1.0.0`, "7-step canonical workflow",
`Status: IMPLEMENTED AND COMPLIANT`) in both canonical and compatibility
form. R6 merged current main, ran an expanded census, and repaired 12
files plus 6 broken links.

## CRITICAL INSTRUCTION: do not trust the census count or file list on
faith. Independently inspect every active adapter family yourself --
re-derive the finding, don't just confirm the claimed fix locations.

## Required audit scope -- verify each independently

1. **Main drift.** Run `git fetch --prune origin` then
   `git rev-list --left-right --count HEAD...origin/main` and confirm 0
   behind.

2. **Independently re-discover the adapter-family census, do not jus
   check the claimed 12 files.** Run your own search across
   `docs/03-reference/pr-pipeline/prep/adapters/**` and
   `docs/pr_prep/adapters/**` (all platform subdirectories: claude,
   cursor, gemini, jules, copilot, vibe, codex) for ANY of:
   `TP-PRPS-000`, `7-step`, `seven-step`, `IMPLEMENTED AND COMPLIANT`,
   as a LIVE claim (bold-labelled or checkmarked, e.g. `**Contract**:`,
   `**Status**: ✅`, `- ✅`) as opposed to retrospective prose that quotes
   the retired term in single backticks while describing it as
   "previously claimed" / "retired" / "superseded". Read every adapter
   README file (both canonical and compat, all 7 platforms) yourself in
   full -- do not rely solely on grep. Report every platform family
   individually: is its canonical readme.md clean? Is its compa
   readme-2.md clean?

3. **Independently verify link resolution, not just the 6 claimed
   fixes.** Write and run your own script (or manual checks) tha
   extracts every markdown relative link from every non-archive file
   under `docs/pr_prep/**` and confirms it resolves to an existing file on
   disk. Do not limit yourself to the 6 files the implementer says were
   fixed -- scan the whole `docs/pr_prep/**` tree yourself and report any
   link you find broken, fixed or not.

4. **The 4 originally-flagged live review threads are resolved.**
   Independently confirm these 4 specific links now resolve:
   - `docs/pr_prep/adapters/vibe/operator-review-form.md` canonical link
   - `docs/pr_prep/adapters/vibe/checkpoint-sequence.md` canonical link
   - `docs/pr_prep/adapters/codex/readme-2.md` canonical link
   - `docs/pr_prep/adapters/vibe/guardrails-2.md` canonical link

5. **Retired-prose files were not accidentally touched or broken.** Spo
   check at least 3 of the 20 files classified `RETIRED_PROSE` (no
   touched by R6) from
   `proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/R6_SCOPE_FREEZE.md` and confirm
   they remain byte-unchanged since R4/prior rounds and are still
   correctly retrospective (not live active claims).

6. **Governance tests pass.** Run
   `python -m pytest tests/governance/test_pr_prep_contract_v2.py tests/governance/`
   and confirm all pass (expect 134 for the single file, 157 for the full
   governance directory).

7. **Task packet still schema-valid, and the R6 allowlist additions are
   present.** Run
   ```
   python3 -c "
   import sys; sys.path.insert(0, 'src')
   from dopemux.orchestrator.validation.packets import validate_packet_file
   print(validate_packet_file('task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json'))
   "
   ```
   confirm status=PASS, 0 errors. Then confirm the 12 new adapter
   canonical/compat paths (claude, cursor, gemini, jules, copilot -- vibe
   was already present) appear in the packet's `commit.allowlist`.

8. **Pre-commit clean on the R6-changed file set.** Run
   `git diff --name-only 4faa2d40a47b95713f5353f7e0d0f8e64b9e57af..ecab6aba71e204fc47337bee13b37e1b715dc37d`
   to get the exact changed-file list, then
   `pre-commit run --files <that list>` and confirm all hooks Passed or
   Skipped with zero file modifications.

9. **Overall coherence.** Is R6 genuinely a complete, correctly-scoped
   closure of the false-negative census -- zero live V1 adapter contrac
   claims anywhere in the non-archive PR-prep canonical/compatibility
   trees, zero broken relative links anywhere in `docs/pr_prep/**`, with
   no unrelated content touched? If you find ANY remaining live V1 claim
   or broken link anywhere in these trees (even outside the 12+6 files
   the implementer named), treat it as a blocking finding -- that would
   mean the census is STILL incomplete.

## Required output forma

Produce a verdict: PASS, PASS_WITH_RISKS, FAIL, or NEEDS_SUPERVISOR. Lis
findings per numbered scope item, noting what you executed vs. took on
faith. Be adversarial about item 2 and item 3 in particular -- the whole
reason R6 exists is that a prior census silently missed things by trusting
its own pattern list; do not repeat that mistake by trusting the
implementer's claimed file list without independently re-deriving it.
