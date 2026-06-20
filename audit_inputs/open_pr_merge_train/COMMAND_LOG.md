# Open PR Merge Train Command Log

Packet: `GB-DMX-OPEN-PR-MERGE-TRAIN-001`
Run: 2026-06-17

## Preflight

```bash
git rev-parse --show-toplevel
# /Users/hue/code/dopemux-mvp

git status --short --branch
# main...origin/main [behind 6] + local dirty/untracked

git remote -v
# origin https://github.com/DDD-Enterprises/dopemux-mvp.git

git fetch origin --prune
# success

gh repo view DDD-Enterprises/dopemux-mvp --json nameWithOwner,defaultBranchRef
# defaultBranchRef.name = main

gh pr list --repo DDD-Enterprises/dopemux-mvp --state open --limit 100 --json ...
# 26 open PRs (see OPEN_PR_LEDGER.json)
```

## #908 Verification

```bash
gh pr view 908 --json state,mergedAt,mergeCommit
# state=MERGED mergeCommit.oid=12b3793fe3944f7677132543d80ee31a4d2637b9
```

## #909 Active PR Work

Worktree: `/Users/hue/.codex/worktrees/ae46/dopemux-mvp`

### Initial state
- head: `414bf8e9d74e5259c356d9601a9eec5b809e26f2`
- base: `12b3793fe3944f7677132543d80ee31a4d2637b9`
- mergeable: MERGEABLE
- checks: all SUCCESS on prior head
- unresolved active threads: 1 (route-decision deserialization scope)

### Repair commit
```bash
# Expanded 0007 packet allowlist/steps for RouteDecision.from_dict + routing_model tests
git commit -m "docs(dcp): include RouteDecision deserialization in 0007 scope"
# b147009231a49263c9104ca1273f42b55793678b

git push origin feat/dcp-0007-input-provenance-contract
# success
```

### Validation (on repair commit)
```bash
python -m json.tool task-packets/DMX-DCP-MODEL-ROUTING-MVP-0007.json >/dev/null  # exit 0
python structural check  # PASS
python -m jsonschema -i task-packets/DMX-DCP-MODEL-ROUTING-MVP-0007.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json  # exit 0
git diff --check  # exit 0
```

### Review thread resolution
```bash
gh api graphql resolveReviewThread threadId=PRRT_kwDOPyIw986KER6f
# isResolved=true (route-decision deserialization thread)
```

### Final merge gate (head b14700923)
- checks: 0 pending, 0 failures (22 success + 3 skipped)
- unresolved active threads: 0
- outdated unresolved threads: 0
- mergeable: MERGEABLE

```bash
gh pr merge 909 --repo DDD-Enterprises/dopemux-mvp --rebase --match-head-commit b147009231a49263c9104ca1273f42b55793678b
# exit 0

gh pr view 909 --json state,mergeCommit
# state=MERGED mergeCommit.oid=0c521642c0e5c6d63a7b719249e30f2a61ff9a74
```

## Stop Condition
Per packet: stop after #909 merged. Did not touch #906, #915, or other PRs.
