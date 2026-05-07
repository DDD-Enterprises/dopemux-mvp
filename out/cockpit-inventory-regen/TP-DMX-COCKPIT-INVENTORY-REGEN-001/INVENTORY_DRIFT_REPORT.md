# Inventory Drift Report

Packet: `TP-DMX-COCKPIT-INVENTORY-REGEN-001`

Compared source HEAD: `b6b89fae076a669952ef1178d7d7d17a3e01eb7b`

## Result

The carried aggregate command inventory remains count-stable against the accepted artifacts. Current regeneration is aggregate-only because the accepted artifacts do not expose complete row records. This packet records the freshness blocker as addressed by current-head artifacts, but it does not reclassify command rows or resolve downstream drift.

## Count Comparison

| Metric | Accepted | Regenerated | Classification |
| --- | ---: | ---: | --- |
| Total inventory rows | 405 | 405 | `SAME` |
| Active rows | 366 | 366 | `SAME` |
| Settings/Admin rows | 62 | 62 | `SAME` |
| Unknown/Drift lower-bound queue items | 487 | 487 | `SAME` |
| T4 policy-missing block | 1 | 1 | `SAME` |
| Stale proof count | 1 | 1 | `SAME` |
| Accepted index drift count | 1 | 1 | `STALE_INPUT` |

## Uncomparable / Decision Items

| Item | Classification | Reason |
| --- | --- | --- |
| Settings/Admin per-row tier mapping | `NEEDS_PACKET_DECISION` | 62 rows are proven, but per-row tiers are not. |
| TX exact row count | `UNCOMPARABLE` | Blocked and deprecated aggregate axes may overlap. |
| TU exact row count | `UNCOMPARABLE` | Unknown axes overlap without row records. |
| Runtime `dopemux help` resolution | `STALE_INPUT` | Accepted residual remains unresolved; this packet did not invoke live runtime discovery. |

## Preserved Drift

- Remote-mutation policy remains absent; `T4` remains blocked.
- Unknown/Drift rows remain non-executable and require packet evidence.
- `TX` and `TU` remain non-executable.
- Claude Design final screens remain blocked.
- Per-row gaps remain visible as `UNKNOWN`, not silently resolved.
