# Stack State Report

Packet: `TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001`
Generated: `2026-05-04T22:43:10Z`

| PR | Packet | Base | Head | Expected head match | State | Draft | Mergeable | Checks | Classification input |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 568 | `TP-DMX-COCKPIT-RUNTIME-RENDER-001` | `pack/cockpit-pack-remediate-006-ia` | `codex/cockpit-runtime-render-001` | True | OPEN | False | MERGEABLE | {'SKIPPED': 3, 'SUCCESS': 12} | PASS |
| 569 | `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001` | `codex/cockpit-runtime-render-001` | `codex/cockpit-settings-runtime-001` | True | OPEN | False | MERGEABLE | {'SKIPPED': 3, 'SUCCESS': 12} | PASS_WITH_RISKS |
| 570 | `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001` | `codex/cockpit-settings-runtime-001` | `codex/cockpit-unknown-drift-001` | True | OPEN | False | MERGEABLE | {'SKIPPED': 10, 'SUCCESS': 12} | PASS |
| 571 | `TP-DMX-COCKPIT-INVENTORY-REGEN-001` | `codex/cockpit-unknown-drift-001` | `codex/cockpit-inventory-regen-001` | True | OPEN | False | MERGEABLE | {'SKIPPED': 10, 'SUCCESS': 12} | PASS |

## Artifact Drift

- Accepted inventory status artifact records `current_head` as the prior upstream head while the PR 571 remote head is the audited final head; this packet records the drift and does not rewrite accepted upstream artifacts.

## Boundary

No pull request merge, base retarget, rebase, force-push, or branch deletion operation was performed by this packet.
