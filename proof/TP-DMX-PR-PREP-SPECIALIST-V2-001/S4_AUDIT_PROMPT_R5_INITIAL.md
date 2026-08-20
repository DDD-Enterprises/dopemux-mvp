You are an INDEPENDENT L2 auditor for a docs-governance repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family
(Gemini) from the implementer (Claude Sonnet). Verify independently by
reading files and running commands yourself in the current working
directory: /Users/hue/code/dopemux-mvp, branch
feat/pr-prep-specialist-v2-contract (already checked out).

## Packet under audit

TP-DMX-PR-PREP-SPECIALIST-V2-001, round R5. PR #1224,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1224, base main, head
(merge commit) a89c11dbfd9d132797575118f3f7b8c4f819a2ab.

## Why R5 exists

R4 (commit 6f32ac97dfd64f4386182fdd24380b2817551303, already independently
audited PASS per proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/AUDITOR_REPORT.md)
was ready, but the branch was 19 commits behind origin/main and GitHub
branch protection requires the PR head to be up to date with main before
merge. The operator authorized a normal merge of origin/main into the
branch (not rebase, not squash, no force-push), conditioned on pre-merge
drift classification showing zero file-path overlap between the branch's
own changed files and main's drift. R5
(a89c11dbfd9d132797575118f3f7b8c4f819a2ab) is the result of that merge.

## Required audit scope -- verify each independently

1. **Merge is a real, non-fast-forward merge commit.** Run
   `git log --pretty=%P -1 a89c11dbfd9d132797575118f3f7b8c4f819a2ab` and
   confirm two parent hashes: `88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c`
   (old branch head) and `6626aa9a58dd82e62226cfca63498cc3f711bb75` (main at
   merge time). Confirm this is not a rebase or squash.

2. **No conflict markers, no content collision on this packet's own
   files.** Run
   `git diff 6f32ac97dfd64f4386182fdd24380b2817551303..a89c11dbfd9d132797575118f3f7b8c4f819a2ab -- docs/03-reference/pr-pipeline docs/pr_prep tests/governance/test_pr_prep_contract_v2.py task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.md`
   and confirm it is EMPTY (the merge introduced zero changes to this
   packet's own content -- it came through byte-identical from R4). Also
   grep the whole tree for unresolved conflict markers:
   `grep -rln '^<<<<<<<$\|^=======$\|^>>>>>>>' --include='*.md' --include='*.json' --include='*.py' . 2>/dev/null | grep -v '/\.git/'`
   and confirm no real hits.

3. **Main-drift content is what it claims to be.** Run
   `git diff 88c3cc73cdcd7c5373beae41a17c5c8a1c76f56c..6626aa9a58dd82e62226cfca63498cc3f711bb75 --stat`
   and confirm the drift does not touch `docs/03-reference/pr-pipeline/**`,
   `docs/pr_prep/**`, `tests/governance/**`, or
   `task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.*` -- i.e. main's changes
   are disjoint from this packet's owned files.

4. **Governance tests pass post-merge.** Run
   `python -m pytest tests/governance/test_pr_prep_contract_v2.py tests/governance/`
   and confirm all pass (expect 69 passed for the single file, 92 passed
   for the full governance directory -- no regression from R4).

5. **Task packet still schema-valid.** Run
   ```
   python3 -c "
   import sys; sys.path.insert(0, 'src')
   from dopemux.orchestrator.validation.packets import validate_packet_file
   print(validate_packet_file('task-packets/TP-DMX-PR-PREP-SPECIALIST-V2-001.json'))
   "
   ```
   and confirm status=PASS, 0 errors.

6. **The known pre-existing docs-prohibited-patterns false positive is now
   resolved.** Run
   `pre-commit run --files docs/pr_prep/adapters/vibe/template-agent.md`
   and confirm the "Block prohibited documentation patterns" hook now
   PASSES (this was a documented pre-existing failure at R4, fixed upstream
   by PR #1225 and pulled in via this merge -- confirm it is actually
   fixed, don't take this claim on faith).

7. **origin/main drift.** Run `git fetch --prune origin` then
   `git rev-list --left-right --count HEAD...origin/main` and confirm 0
   behind (branch is fully up to date with main after the merge).

8. **Overall coherence.** Is R5 genuinely just "R4's already-audited
   content plus an unrelated, non-conflicting slice of main, combined via a
   real merge commit, with zero semantic change to this packet's docs,
   tests, or task-packet content"? State your verdict plainly. If you find
   ANY change to this packet's own governed content versus R4, treat it as
   a blocking finding.

## Required output format

Produce a verdict: PASS or FAIL (or NEEDS_SUPERVISOR). List findings per
numbered scope item, noting what you executed vs. took on faith.
