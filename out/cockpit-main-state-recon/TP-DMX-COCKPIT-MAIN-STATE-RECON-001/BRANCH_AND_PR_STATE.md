# BRANCH_AND_PR_STATE — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

As of 2026-05-07.

## Branch heads

| Branch | HEAD SHA | Subject |
| --- | --- | --- |
| `origin/main` | `d52fbf1b8786b27305afb6c52ac294ba7a12f2d5` | fix(extraction): preserve lexical BM25 matches |
| `origin/pack/cockpit-pack-remediate-006-ia` | `b173efd83c871c30f2bd86530921c866d08e7e45` | docs(cockpit): regenerate current head inventory (#571) |

Pack vs main: pack is **ahead 18 / behind 9**. **196 files differ.**

## Cockpit PR state matrix

| PR | Title | State | Base | Head OID | Merge Commit | In `origin/main`? | In pack? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #568 | ui(cockpit): wire runtime renderer primitives to IA package | MERGED | pack/...006-ia | `9ad522df3` | `39ad991f7` | **NO** | YES |
| #569 | ui(cockpit): wire settings runtime primitives | MERGED | pack/...006-ia | `d27c4995f` | `a4ca22da6` | **NO** | YES |
| #570 | ui(cockpit): wire unknown drift queue primitives | MERGED | pack/...006-ia | `b6b89fae0` | `7ff3ea44e` | **NO** | YES |
| #571 | docs(cockpit): regenerate current head inventory | MERGED | pack/...006-ia | `93702834f` | `b173efd83` | **NO** | YES (= pack HEAD) |
| #572 | docs(cockpit): prepare merge stack consolidation | **OPEN** | pack/...006-ia | `23ec8b70f` | n/a | NO | NO |
| #573 | fix(cockpit): repair runtime contract fidelity gaps | **OPEN** | pack/...006-ia | `1236757c1` | n/a | NO | NO |

## Containment evidence

ancestry probe (`merge-base --is-ancestor`) results:

- `39ad991f7…04fc` (PR 568 merge commit): in `origin/main` = **NO**, in pack = **YES**.
- `a4ca22da…80d4` (PR 569 merge commit): in `origin/main` = **NO**, in pack = **YES**.
- `7ff3ea44…ae65e` (PR 570 merge commit): in `origin/main` = **NO**, in pack = **YES**.
- `b173efd8…8e7e45` (PR 571 merge commit): in `origin/main` = **NO**, in pack = **YES** (it is the pack HEAD).

## CI status (open Cockpit PRs)

- PR 572: every required check completed `SUCCESS`; remaining advisory checks `SKIPPED`. GitHub mergeable.
- PR 573: every required check completed `SUCCESS`; Gemini Dispatch advisory steps `SKIPPED`. GitHub mergeable.

CI status is observed evidence; it is **not** an authorization to land work on `origin/main`.

## Cross-reference between open Cockpit PRs

- PR 572 body does **not** reference PR 573.
- PR 573 body does **not** reference PR 572.

PR 573 was opened after PR 572 began documenting stack readiness. PR 572's stack readiness verdict therefore did not audit PR 573's runtime-contract changes. This is recorded as a drift item in `GAP_AND_DRIFT_REPORT`.

## Non-actions performed

- no PR merges performed
- no branch retargeting performed
- no rebase performed
- no force push performed
- no branch deletion performed
- no PR edits performed
- no PR closes performed
