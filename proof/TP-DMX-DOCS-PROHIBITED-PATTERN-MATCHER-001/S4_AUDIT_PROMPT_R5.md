You are an INDEPENDENT S4 auditor for a small CI-trust-policy repair packet in the
dopemux-mvp repository. You are a separate CLI process and model family (Gemini)
from the implementer (Claude Sonnet). Verify independently by reading files and
running commands yourself in the current working directory (git worktree for
branch fix/docs-prohibited-pattern-matcher-001, already checked out).

## Packet under audit

TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001, round R5. PR #1225,
https://github.com/DDD-Enterprises/dopemux-mvp/pull/1225, base main, head
c44f09b6ec6ae80236acc1dd02a749abf62ecd79.

## Why R5 exists

R4 (commit d1c261a80717ff37f7b62034e8e6a25e4c405d29, already independently
audited PASS) was ready to merge, but GitHub branch protection required the
PR head to be up to date with main (main had advanced by two commits since
the branch was created). The operator authorized a normal merge of
origin/main into the branch (not rebase, not squash, no force-push). R5
(commit c44f09b6ec6ae80236acc1dd02a749abf62ecd79) is the result of that
merge.

## Required audit scope — verify each independently

1. **Merge is a real, non-fast-forward merge commit.** Run
   `git log --oneline -3 c44f09b6ec6ae80236acc1dd02a749abf62ecd79` and
   `git show c44f09b6ec6ae80236acc1dd02a749abf62ecd79 --stat | head -5` to
   confirm this is a merge commit (two parents) rather than a rebase or
   squash. Run
   `git log --pretty=%P -1 c44f09b6ec6ae80236acc1dd02a749abf62ecd79` and
   confirm two parent hashes are listed.

2. **No conflict markers, no policy-file collision.** Run
   `git diff d1c261a80717ff37f7b62034e8e6a25e4c405d29..c44f09b6ec6ae80236acc1dd02a749abf62ecd79 -- .pre-commit-config.yaml scripts/ci/docs_prohibited_patterns.sh tests/ci/test_docs_prohibited_patterns.py task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json`
   and confirm it is EMPTY (i.e. the merge introduced zero changes to this
   packet's own files — they came through byte-identical from R4). Also
   grep the whole tree for unresolved conflict markers:
   `grep -rn '^<<<<<<<\|^=======$\|^>>>>>>>' --include='*.sh' --include='*.py' --include='*.json' --include='*.yaml' . | grep -v '/\.git/'` and confirm no hits (except expected false positives you should manually judge, e.g. inside this very prompt file if it's in-tree, which it should not be).

3. **Main-drift content is what it claims to be.** Run
   `git diff 9dce8ffaec489f486d0356d300f0e8ea5aefa3d2..origin/main --stat`
   (or compare against the second parent of the merge commit) and confirm
   the drift is confined to `src/dopemux/mcp/**`, `tests/mcp/**`,
   `docs/03-reference/architecture/second-brain/**`, and
   `proof/**` paths unrelated to this packet (e.g. `proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/**`,
   `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/**`,
   `proof/pr_merge/embedded-audit/pr-1226/**`, `task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.*`,
   `task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT.json`).
   Confirm none of these paths implement or alter any CI trust-policy hook
   (search for "docs-prohibited-patterns" or "pre-commit" mentions in the
   diff; there should be none affecting this packet's hook).

4. **Matcher behavior unchanged and fully correct post-merge.** Run
   `python3 -m pytest tests/ci/test_docs_prohibited_patterns.py -v`
   (expect 22 passed) and independently execute the script against a
   representative sample: allowed (`docs/pr_prep/adapters/vibe/template-agent.md`,
   `docs/03-reference/governance/task-packet-template.md`) and forbidden
   (`docs/scratch/temp.md`, `docs/scratch/notes-template.md`,
   `docs/scratch/todo-template.md`) — confirm results match all prior
   rounds (R1-R4).

5. **Task packet still schema-valid.** Validate
   `task-packets/TP-DMX-DOCS-PROHIBITED-PATTERN-MATCHER-001.json` against
   `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` with
   `jsonschema.Draft7Validator` — expect zero errors.

6. **Shell quality.** `bash -n` and `shellcheck` on
   scripts/ci/docs_prohibited_patterns.sh — both clean.

7. **Full-tree hook safety.** Run
   `pre-commit run --all-files docs-prohibited-patterns` and confirm it
   passes with no unexpected new flags (the MCP/second-brain files pulled
   in by the merge are not docs/*.md or task-packets/*.md files subject to
   this hook, so nothing new should be flagged or un-flagged).

8. **Overall coherence.** Is this genuinely just "R4's already-audited
   content plus an unrelated, non-conflicting slice of main, combined via a
   real merge commit, with zero semantic change to the CI-policy fix or its
   tests"? State your verdict plainly. If you find that the merge
   introduced ANY change to the matcher logic, tests, or task-packet
   content versus R4, treat it as a blocking finding.

## Required output format

Produce a verdict: PASS or FAIL (or NEEDS_SUPERVISOR). List findings per
numbered scope item, noting what you executed vs. took on faith.
