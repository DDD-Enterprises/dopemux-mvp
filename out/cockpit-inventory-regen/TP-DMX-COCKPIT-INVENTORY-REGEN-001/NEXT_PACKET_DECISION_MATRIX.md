# Next Packet Decision Matrix

Packet: `TP-DMX-COCKPIT-INVENTORY-REGEN-001`

This matrix recommends downstream packet direction from regenerated evidence only. It does not approve final screens, remote mutation, runtime execution, or row reclassification.

| Candidate packet | Recommendation | Evidence | Boundary |
| --- | --- | --- | --- |
| Remote-mutation policy packet | Recommended | `T4` remains blocked and the remote-mutation policy reference is absent. | Policy only; no remote mutation is authorized here. |
| Additional UNKNOWN resolution packet | Recommended | Unknown/Drift lower-bound remains 487, Settings/Admin still has 62 unknown-tier rows, and authority/root-schema gaps remain. | Must classify rows by packet evidence only. |
| Merge/stack consolidation packet | Recommended | PR chain 568 -> 569 -> 570 remains stacked, and this packet bases on PR 570. | Consolidation should preserve accepted artifacts and proof. |
| Claude Design primitive/final-screen unlock packet | Not recommended | Unblock conditions are not all satisfied: remote policy missing, per-row data gaps remain, root authority/schema gaps remain, and UNKNOWN classes remain unresolved. | Do not generate or upload final screens. |
| Runtime renderer behavior packet | Not recommended from this evidence | Current runtime-render primitives already expose required modes, surfaces, Settings/Admin, Unknown/Drift, and Safe Action tier status. | Do not edit runtime behavior without a proven inventory bug. |

## Required Current Governance

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- no final screens
- no Claude Design upload
- no runtime action execution
- no T4 remote mutation
- no live service adapters
- no canonical writes
- no runtime reclassification
