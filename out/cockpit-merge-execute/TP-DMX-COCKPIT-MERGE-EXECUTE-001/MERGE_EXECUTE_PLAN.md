# TP-DMX-COCKPIT-MERGE-EXECUTE-001 Merge Execute Plan

## Scope

This artifact defines a later Ledger-authorized Cockpit pack consolidation procedure. It does not execute a merge and does not authorize any executor to proceed without a separate explicit Ledger authorization.

Non-actions in this packet:

- Do not merge PR #572.
- Do not merge PRs #568, #569, #570, or #571.
- Do not rebase.
- Do not force-push.
- Do not retarget or close PRs.
- Do not modify runtime source.
- Do not change Cockpit UI runtime code.
- Do not upload to Claude Design.
- Do not generate final screens.
- Do not authorize runtime execution.
- Do not authorize T4 remote mutation.
- Do not authorize TX/TU execution.
- Do not enable Unknown/Drift runtime reclassification.
- Do not authorize canonical writes.

## Evidence To Carry Forward

PR #572:

- URL: https://github.com/DDD-Enterprises/dopemux-mvp/pull/572
- Post-conflict-fix re-audit verdict: `PASS_WITH_RISKS_READY_FOR_MERGE_EXECUTE_PACKET`
- Current audited head: `e28db50f2c4fc06819cb278da1e149afd7e39d49`
- Audit base main: `4206a297232f6398df1964431c7b56ecbf931d82`
- Audit state: `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`, `25 SUCCESS / 3 SKIPPED / 9 IN_PROGRESS`, no failing checks, empty `reviewDecision`
- Conflict repair: `task-packets/INDEX.md` conflict resolved
- Audit merge-tree result: `d5d28ae60af977c17dbe860a1d53c8e5859015f2`

Packet-authoring observations on 2026-05-08:

- Git branch API and `git ls-remote` observed `refs/heads/main` at `4206a297232f6398df1964431c7b56ecbf931d82`.
- GitHub PR APIs observed PR #572 head at `e28db50f2c4fc06819cb278da1e149afd7e39d49`.
- GitHub PR APIs observed `mergeable=MERGEABLE`, `mergeStateStatus=UNSTABLE`, empty `reviewDecision`, and checks at `33 SUCCESS / 3 SKIPPED / 1 IN_PROGRESS`.
- GraphQL `baseRef.target.oid` matched `4206a297232f6398df1964431c7b56ecbf931d82`; GraphQL `baseRefOid` and REST `base.sha` reported `0ca8fae9dee59bc410cf013cc9af741aa28b88e7`. This mismatch is drift to resolve during future preflight.
- Merge-tree against `4206a297232f6398df1964431c7b56ecbf931d82` returned clean tree `d5d28ae60af977c17dbe860a1d53c8e5859015f2`.
- Merge-tree against the API-reported `0ca8fae9dee59bc410cf013cc9af741aa28b88e7` surfaced a content conflict in `docker/mcp-servers-source/desktop-commander/server.py`; because `refs/heads/main` was observed at `4206a297232f6398df1964431c7b56ecbf931d82`, this is recorded as API/base drift, not as a current merge execution result.
- Commit `e28db50f2c4fc06819cb278da1e149afd7e39d49` is a single-parent commit with parent `f91b7784a1135a8d30b5c58787235f1a70f708ca`, despite merge-like content.

Covered PR set:

- PR #568
- PR #569
- PR #570
- PR #571
- PR #573

## Merge Candidate Order

The future Ledger-authorized executor must process candidate evidence in this order:

1. PR #568
2. PR #569
3. PR #570
4. PR #571

PR #573 is reviewed merged evidence only. It is not a merge candidate for this procedure. Its observed merge commit is `c0c32c1639e675d3415257f2444437ae1fa2ea3c`.

PR #572 is the consolidation artifact/proof PR. It is not self-authorizing. Execution requires explicit Ledger authorization after all preflight gates pass.

## Preflight Gate

Before any future merge execution, the executor must re-check and record:

- Repo identity, including `.dopetaskroot` marker and `origin` URL.
- Clean worktree.
- Current `origin/main`.
- Current PR #572 head.
- PR #572 still descends from `e28db50f2c4fc06819cb278da1e149afd7e39d49`.
- PR #572 mergeable state.
- PR #572 status checks settled with no required failures.
- `reviewDecision` and branch protection status.
- Merge-tree clean against current `origin/main`.
- No runtime source changes appear unexpectedly in the execution diff.
- Governance invariant exact matches.
- Stale `PROOF.json` conflict text is treated only as a historical generation-time snapshot, not current merge state.

## Stop Conditions

Stop without mutation if any condition appears:

- PR #572 becomes `DIRTY` or `CONFLICTING`.
- PR #572 no longer descends from `e28db50f2c4fc06819cb278da1e149afd7e39d49`.
- Required checks fail.
- Required review is missing.
- Merge-tree conflict appears against current `origin/main`.
- Runtime source changes appear unexpectedly.
- Any artifact claims Claude Design readiness.
- Any artifact claims final-screen readiness.
- Any artifact claims runtime execution readiness.
- Any artifact claims T4 readiness.
- Any artifact claims Unknown/Drift runtime reclassification readiness.

## Future Proof Requirements

The future executor must produce exactly one JSON proof bundle at closeout. It must include:

- Command outputs and exit codes.
- Branch/head/base SHAs.
- Merge-tree output.
- Checks and `reviewDecision` state.
- Changed files.
- Commit or merge SHAs.
- Final git status.
- Explicit no-runtime, no-Claude-Design, no-T4, and no-reclassification confirmation.

