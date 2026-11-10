---
name: pr-merge-specialist
description: Use when draining dopemux-mvp pull requests, a GitHub merge queue is enabled, a signed embedded audit is bound to a pull request head, or a session is about to run pr-merge flight, auto-pilot, queue-drain, gh pr update-branch, or gh pr merge.
---

# Skill: PR Merge Specialist

## Purpose
Land pull requests through the legal path for the current base branch. A signed embedded audit belongs to the current head. A new head needs a new audit.

## GitHub merge queue
When the base branch has an active GitHub merge queue, that queue is the merge path.

Enqueue one non-draft pull request at a time. Both of these checks must be success on the current head: `independent embedded audit` and `PR Steward / final readiness`.

```bash
gh pr merge <n> --repo DDD-Enterprises/dopemux-mvp --merge
```

Leave the branch in place. The queue's `merge_method` is the merge method.

Stop, and do not run any of these, while that queue is active:

- `dopemux pr-merge flight --auto-pilot`
- `dopemux pr-merge queue-drain`
- `gh pr update-branch`
- `gh pr merge` with `--rebase`, `--squash`, `--delete-branch`, or `--admin`
- force-push
- resolving a review thread whose finding is still true
- marking a draft ready

`dopemux pr-merge flight` without `--auto-pilot` may scan. A scan must not rebase, merge, delete a branch, or resolve a thread.

`merge.py`, `queue_drain.py`, and `worktree.py` still emit `gh pr update-branch --rebase` and `gh pr merge --rebase --delete-branch`. Those commands stay unused while the queue is active. A green dry-run does not clear them.

## Operator authority
Merging, marking ready, closing, or enabling auto-merge needs explicit operator authority (AGENTS.md §9). Auto-pilot and queue-drain need that authority even when no merge queue is active.

## When not to use
- Architectural design.
- A required human security review, an admin bypass, or a solo-owner security phrase posted against a head that will still change.

## Mandates
- Stacked pull requests move in dependency order.
- Conflicts under `auth/` or `secrets/` go to a human.
- Ambiguity stops for a human decision.
- Log every automated action.
- Throughput does not override the queue rules above.
