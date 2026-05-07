# Cockpit Command / Surface Inventory

Packet: `TP-DMX-COCKPIT-INVENTORY-REGEN-001`

Generated at UTC: `2026-05-04T21:53:46Z`

Base/current source HEAD inspected: `b6b89fae076a669952ef1178d7d7d17a3e01eb7b`

Governance state:

- `safe_for_claude_design: NO`
- `READY_FOR_CLAUDE_DESIGN: not approved`
- `ia_verdict: CURRENT_COCKPIT_IA_NEEDS_MAJOR_RECONCILIATION`

## Source Status

The accepted artifacts expose command/surface counts and examples, but not a complete current per-row inventory. This regeneration therefore preserves aggregate records and labels row-level precision as unavailable. No accepted upstream artifact was modified.

Runtime sources inspected:

- `src/dopemux/ui/cockpit/__init__.py`
- `src/dopemux/ui/cockpit/app.py`
- `src/dopemux/ui/cockpit/render.py`
- `src/dopemux/ui/cockpit/runtime_contract.py`
- `src/dopemux/commands/cockpit_commands.py`

## Regenerated Counts

| Axis | Count / status | Evidence |
| --- | ---: | --- |
| Total carried inventory rows | 405 | `COMMAND_EXPOSURE_POLICY.json`, `PACKAGE_REMEDIATION_INDEX.json` |
| Active rows | 366 | accepted carried counts |
| Per-row records emitted | 0 | per-row inventory unavailable in accepted artifacts |
| Aggregate records emitted | 16 | this artifact |
| Settings/Admin rows | 62 | accepted package count |
| Settings/Admin unknown-tier rows | 62 | accepted Settings/Admin proof |
| Unknown/Drift lower-bound queue items | 487 | accepted Unknown/Drift proof |
| Unknown/Drift aggregate item records | 45 | accepted Unknown/Drift proof |
| T4 policy-missing block | 1 | Safe Action refusal rules and runtime snapshot |
| Stale proof count | 1 | accepted Unknown/Drift proof |
| Index drift count carried from accepted Unknown/Drift proof | 1 | accepted Unknown/Drift proof |

## Runtime Model Preserved

Top-level modes:

1. `PM`
2. `Implementer`
3. `Overview`
4. `Services`
5. `Events`

Global surfaces:

1. `Command Palette`
2. `Settings/Admin/Runtime`
3. `Safe Actions / Proof Gate`
4. `Unknown / Drift Queue`

Safe Action tiers remain `T0`, `T0i`, `T1`, `T2`, `T3`, `T4`, `T5`, `T6`, `TX`, `TU`. `T4` remains blocked until a separate accepted remote-mutation policy exists. `TX` and `TU` remain non-executable.

## Aggregate Policy

Aggregate records are used where accepted artifacts do not expose complete row data. A count can be high-confidence while its row-level `source_ref`, `canonical_writer`, `gate_tier`, and exact `proof_requirement` remain `UNKNOWN` or mixed.

This packet does not resolve drift, promote rows, demote rows, wire service adapters, authorize remote mutation, execute actions, or approve final screens.
