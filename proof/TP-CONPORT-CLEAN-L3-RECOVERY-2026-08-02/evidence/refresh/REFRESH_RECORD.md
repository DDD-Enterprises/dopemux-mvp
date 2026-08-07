# PR #1188 main refresh record

| Field | Value |
|---|---|
| old_branch_tip | `2f4303a1be8a49ecd4ab280d3523a09adbb69cbc` |
| refreshed_main_sha | `fb710ef40500695882a5b421a3325150176fffa1` |
| previous_main_anchor | `fafc85e31f20c452f0c7d1e9dbaf95bc9e0ffbe1` |
| merge_base_post | `fb710ef40500695882a5b421a3325150176fffa1` |
| merge_commit | `5ab419b9e3236f17add2c2d09ac22efde942500e` |
| overlap_classification | **COMPATIBLE** (0 path intersection) |
| merge_strategy | `git merge --no-ff origin/main` (no rebase, no force-push) |
| main_moves_since_anchor | `#1182` replan/orchestrator annotation only (docs/proof/load-plans) |
| recovery_impl_blob_identity | all 13 non-proof implementation paths **IDENTICAL** to old tip (see patch_identity_post_merge.txt) |
| #1182 in PR delta | **NONE** |
| policy.json in PR delta | **NONE** (inherited from main via #1187) |

## Ancestry

```
*   5ab419b9e3 merge(main): refresh clean L3 recovery branch onto current main
|\
| * fb710ef405 replan(orchestrator): full 539-item wave+runner+luna-ready annotation (#1182)
| * fafc85e31f fix(pr-steward): restore packaged check_only policy scaffold (#1187)
| * 7f75f9e0ad feat(governance): evidence-economy execution and pre-push contract gate (#1184)
* | 2f4303a1be proof(conport): clarify clean L3 head classification for auditors
* | 74c15e8185 proof(conport): pin clean L3 PROOF head_sha to tip
* | e7aec96769 proof(conport): clean L3 candidate evidence for PID1, wall, row cleanup
* | 6f4d6b11e3 fix(conport): pin info_server MCP_SERVER_PORT so discovery binds :4004
* | ada30f8fc9 fix(conport): PID1 fail-closed supervision; drop autoheal; lock legacy archive
* | 80e3ed2f42 fix(conport): project wall, 2025 corpus recovery, stop silent outage
|/
* 525ddb5fe5 fix(audit): fail-closed PAL clink JSON parse (fence-only salvage) (#1181)
* 899082ae74 🎨 Palette: Add Tooltip to Pending Task Start Buttons in TaskSequencer (#1177)
```

## Paths introduced by main (not in PR delta)

See `git diff --name-only 2f4303a1be8a49ecd4ab280d3523a09adbb69cbc^2..origin/main` / merge parents. PR delta remains the 51 recovery paths only.

## Supersedes

Stale head bindings on pre-refresh tip `2f4303a1be8a49ecd4ab280d3523a09adbb69cbc` are superseded by post-validation content head (to be frozen after L3 probes). Historical evidence under `evidence/` retained; not rewritten.
