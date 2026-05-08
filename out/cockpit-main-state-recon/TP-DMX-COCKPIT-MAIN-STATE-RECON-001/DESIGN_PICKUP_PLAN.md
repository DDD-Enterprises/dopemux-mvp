# DESIGN_PICKUP_PLAN — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

This plan recommends where this thread should resume design work. It is **not** an authorization to consolidate, upload to Claude Design, generate final screens, execute runtime actions, perform T4 remote mutation, or perform canonical writes. Governance state preserved: `safe_for_claude_design: NO`, `READY_FOR_CLAUDE_DESIGN: not approved`.

## 1. What landed on `origin/main`

**Nothing from the cockpit pack remediation series.** Origin/main HEAD is `d52fbf1b8` (`fix(extraction): preserve lexical BM25 matches`). Cockpit `src/` on main carries only `__init__.py`, `app.py`, `render.py`. There are no `out/cockpit-*` directories on main, no proof tree for the pack series, and no `task-packets/generated/` directory.

## 2. What landed on `pack/cockpit-pack-remediate-006-ia` only

- PRs 568–571 merged into pack: runtime renderer primitives, settings runtime primitives, unknown drift queue primitives, current-head inventory regen.
- `src/dopemux/ui/cockpit/runtime_contract.py` (added in PR 568, modified in 569 and 570).
- 8 `out/cockpit-*` artifact trees and 4 `proof/cockpit-*` proof trees.
- 4 packet JSONs in `task-packets/generated/`.
- Pack diverges from main by 18 commits ahead / 9 commits behind, 196 files differ.

## 3. Open PRs that still affect Cockpit design

| PR | Status | Why it blocks design pickup |
| --- | --- | --- |
| #572 | OPEN_STACKED, all CI green | self-reports `READY_WITH_RISKS_NEEDS_LEDGER_DECISION`; the artifact only audits PRs 568–571 and **does not cover PR 573** |
| #573 | OPEN_RELEVANT, all CI green | modifies pre-existing `src/dopemux/ui/cockpit/runtime_contract.py` and pre-existing test files to repair contract-fidelity gaps; not yet in pack or main |

## 4. Open PRs that should be closed as superseded

None observed in this audit. Both #572 and #573 carry distinct, currently-needed work.

## 5. Open PRs that must be audited before design continues

- **PR #572** must be re-audited so its readiness verdict explicitly accounts for PR #573, **or** PR #573 must land into pack first and PR #572 must be regenerated against the updated pack.
- **PR #573** must receive a runtime-contract review before any operator-initiated consolidation of pack into main.

## 6. Open PRs that block Claude Design

- PR #572 (until Ledger disposes of accepted residual risks: Settings/Admin per-row tier mapping, remote-mutation policy absence, inventory `current_head` drift, root authority/schema gap).
- PR #573 (until runtime-contract repairs are reviewed and a refreshed consolidation artifact covers them).

Both PRs preserve `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved`. This packet preserves the same.

## 7. Open PRs that do not block Cockpit design

- PR #582 (dependabot pip): touches MCP and service `requirements.txt`. Process via standard dependency review track.
- PR #583 (dependabot uv): touches root `pyproject.toml`, `uv.lock`, MCP server lock files. Process via standard dependency review track.
- PR #584 (PR 576 review follow-ups): MCP CLI documentation and tests; the `.claude/modules/coordination/authority-matrix.md` edit is a single-line update of a stale `pm-plane/` reference and **does not touch Cockpit, Claude Design, T4, or Safe Action governance rows**.

## 8. Required inputs before the next design step

1. Ledger disposition of the residual risks PR 572 flagged (Settings/Admin per-row tier mapping, remote-mutation policy absence, inventory `current_head` drift, root authority/schema gap).
2. Review of PR 573's runtime-contract repairs.
3. Refreshed merge-stack consolidation artifact that explicitly covers PR 573 (regenerate `TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001` outputs once PR 573 is reviewed, or produce a successor packet).
4. Authored `TP-DMX-COCKPIT-MERGE-EXECUTE-001` packet (currently `NOT_PRESENT` on either branch).

## 9. Blocked alternatives (do not pursue)

- Resuming Cockpit design work on `origin/main` while the pack remediation surface remains entirely unmerged. Main does not carry the `runtime_contract.py` runtime surface, the cockpit `out/*` artifact trees, the cockpit `proof/*` trees, or the four cockpit packet JSONs.
- Treating PR 572's `READY_WITH_RISKS_NEEDS_LEDGER_DECISION` verdict as authorization to consolidate. Per its own body, PR 572 is artifact-only and **not** merge authorization.
- Treating PR 572 as a complete consolidation gate. It does not audit PR 573.
- Performing remote-mutation policy work on a stacked branch. PR 572 explicitly recommends deferring policy work until the stack lands or the Ledger explicitly authorizes policy work on a stacked branch.
- Bypassing Ledger to perform an ad hoc operator-initiated consolidation of pack into main. Per packet boundaries, no PR merges, retargets, edits, or closes are authorized in this thread.

## 10. Recommended next packet

**`TP-DMX-COCKPIT-MERGE-EXECUTE-001`** — operator-initiated consolidation packet, authored on a Ledger-approved branch. It must:

1. Take input from PR 573 review and a refreshed merge-stack consolidation artifact that includes #573.
2. Take input from a Ledger ruling on the residual risks PR 572 flagged.
3. Stage an operator-initiated consolidation of `pack/cockpit-pack-remediate-006-ia` into `main`, preserving the cockpit packet JSONs, `out/cockpit-*` and `proof/cockpit-*` trees.
4. Avoid all governance escalations: no Claude Design upload, no T4 remote mutation, no canonical writes, no runtime action execution, no runtime reclassification, no final screens.
5. Preserve `safe_for_claude_design: NO` and `READY_FOR_CLAUDE_DESIGN: not approved` until a separately authorized governance packet revisits those fields.

Until that packet exists and runs, **do not** resume Cockpit design work directly on `origin/main`.

## Non-actions performed by this plan

- no PR merges performed
- no PR retargets performed
- no PR edits performed
- no PR closes performed
- no rebases performed
- no force pushes performed
- no Claude Design upload performed
- no final screens generated
- no runtime action execution performed
- no T4 remote mutation performed
- no canonical writes performed
- no runtime reclassification performed
