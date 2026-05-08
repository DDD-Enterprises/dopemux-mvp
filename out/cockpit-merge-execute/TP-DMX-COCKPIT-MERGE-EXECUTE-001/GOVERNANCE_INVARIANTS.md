# TP-DMX-COCKPIT-MERGE-EXECUTE-001 Governance Invariants

These invariants are exact values for this packet and for any later executor consuming it.

| Invariant | Required Value |
| --- | --- |
| `safe_for_claude_design` | `NO` |
| `READY_FOR_CLAUDE_DESIGN` | `not approved` |
| `claude_design_upload` | `not_authorized` |
| `final_screens` | `not_authorized` |
| `runtime_action_execution` | `not_authorized` |
| `t4_remote_mutation` | `not_authorized` |
| `canonical_writes` | `not_authorized` |
| `unknown_drift_runtime_reclassification` | `disabled` |
| `tx_tu_execution` | `disabled` |

## Enforcement Notes

- This packet authorizes packet/proof/governance authoring only.
- This packet does not authorize merge execution.
- This packet does not authorize runtime source changes.
- This packet does not authorize Cockpit UI runtime code changes.
- This packet does not authorize Claude Design upload.
- This packet does not authorize final screens.
- This packet does not authorize T4 remote mutation.
- This packet does not authorize TX/TU execution.
- This packet does not authorize Unknown/Drift runtime reclassification.
- This packet does not authorize canonical writes.
- A later executor must stop if any artifact upgrades these values into readiness or authorization claims.

