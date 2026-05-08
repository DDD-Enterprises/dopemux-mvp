# TP-DMX-COCKPIT-MERGE-EXECUTE-001 Precheck Matrix

Every row is a fail-closed gate for a future Ledger-authorized executor. Passing this matrix does not itself authorize execution; explicit Ledger authorization is still required.

| ID | Gate | Required Evidence | Stop Condition |
| --- | --- | --- | --- |
| P01 | Repo identity | `.dopetaskroot` exists and `origin` is `https://github.com/DDD-Enterprises/dopemux-mvp.git` | Stop if repo marker or origin mismatches. |
| P02 | Clean worktree | `git status --short` has no unexpected changes before execution | Stop if worktree is dirty. |
| P03 | Current `origin/main` | Record `git ls-remote origin refs/heads/main` and local `origin/main` SHA | Stop if base cannot be resolved or authority conflicts remain unresolved. |
| P04 | Current PR #572 head | Record current PR #572 head SHA from GitHub and local fetched ref | Stop if head cannot be fetched. |
| P05 | PR #572 descendant gate | `git merge-base --is-ancestor e28db50f2c4fc06819cb278da1e149afd7e39d49 <current-pr-572-head>` exits 0 | Stop if PR #572 no longer descends from `e28db50f2c4fc06819cb278da1e149afd7e39d49`. |
| P06 | Mergeable state | GitHub reports PR #572 not `DIRTY` or `CONFLICTING` | Stop if PR #572 becomes `DIRTY` or `CONFLICTING`. |
| P07 | Checks settled | Status checks are settled with no required failures | Stop if required checks fail or required checks remain unresolved. |
| P08 | Review and protection | Record `reviewDecision` and branch protection or required-review state | Stop if required review is missing. |
| P09 | Merge-tree | Merge-tree against current `origin/main` is clean | Stop if any merge-tree conflict appears. |
| P10 | Runtime source boundary | Diff for execution path has no unexpected runtime source changes | Stop if runtime source changes appear unexpectedly. |
| P11 | Governance exact matches | Exact invariant values match `GOVERNANCE_INVARIANTS.md` | Stop if any invariant is missing, changed, or upgraded to an authorization. |
| P12 | Stale proof text | Existing stale `PROOF.json` conflict text is classified as historical generation-time snapshot only | Stop if stale conflict text is treated as current merge state or hidden. |

## Mandatory Stop Conditions

- PR #572 becomes `DIRTY` or `CONFLICTING`.
- PR #572 no longer descends from `e28db50f2c4fc06819cb278da1e149afd7e39d49`.
- Required checks fail.
- Required review is missing.
- Merge-tree conflict appears.
- Runtime source changes appear unexpectedly.
- Any artifact claims Claude Design readiness.
- Any artifact claims final-screen readiness.
- Any artifact claims runtime execution readiness.
- Any artifact claims T4 readiness.
- Any artifact claims Unknown/Drift runtime reclassification readiness.

