# RTE-PKT-03 Influence Guard Matrix

| Verdict | Router returned | Scope reduction | Partition reorder/tier hints | Compression hints | Routing hints | Phase hints |
| --- | --- | --- | --- | --- | --- | --- |
| imported_prescan_accepted | yes | allowed only if `prescan_allow_scope_reduction` is true | allowed | allowed | allowed through router APIs | allowed through router APIs |
| imported_prescan_rejected_stale | no | blocked | blocked | blocked | blocked | blocked |
| imported_prescan_missing_metadata | no | blocked | blocked | blocked | blocked | blocked |
| invalid or unparsable import | no | blocked | blocked | blocked | blocked | blocked |
| local_prescan | yes | allowed only if `prescan_allow_scope_reduction` is true | allowed | allowed | allowed through router APIs | allowed through router APIs |
| local_prescan_failed | no | blocked | blocked | blocked | blocked | blocked |
| local_prescan_unavailable | no | blocked | blocked | blocked | blocked | blocked |
| skip_prescan | no | blocked | blocked | blocked | blocked | blocked |

Guard location: `run_integrated_prescan_stage()` now calls `_load_imported_prescan_router()`, which uses `IntelligenceRouter.load_imported()`. A rejected validation returns no router, so the downstream router consumers cannot apply imported skip, compression, partition, routing, or phase hints.

