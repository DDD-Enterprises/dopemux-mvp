# Current HEAD Cockpit Status

Packet: `TP-DMX-COCKPIT-INVENTORY-REGEN-001`

Current source HEAD inspected: `b6b89fae076a669952ef1178d7d7d17a3e01eb7b`

Branch: `codex/cockpit-inventory-regen-001`

PR base: `codex/cockpit-unknown-drift-001`

## Upstream PR Chain

| PR | Head | Base | Status used |
| --- | --- | --- | --- |
| [568](https://github.com/DDD-Enterprises/dopemux-mvp/pull/568) | `codex/cockpit-runtime-render-001` | `pack/cockpit-pack-remediate-006-ia` | accepted with risks |
| [569](https://github.com/DDD-Enterprises/dopemux-mvp/pull/569) | `codex/cockpit-settings-runtime-001` | `codex/cockpit-runtime-render-001` | accepted with risks |
| [570](https://github.com/DDD-Enterprises/dopemux-mvp/pull/570) | `codex/cockpit-unknown-drift-001` | `codex/cockpit-settings-runtime-001` | audit PASS; Ledger request ACCEPT_WITH_RISKS |

## Runtime Model

- Five top-level modes are present: `PM`, `Implementer`, `Overview`, `Services`, `Events`.
- Four global surfaces are present: `Command Palette`, `Settings/Admin/Runtime`, `Safe Actions / Proof Gate`, `Unknown / Drift Queue`.
- Settings/Admin summary is present with 62 accepted rows and 62 unknown-tier rows.
- Unknown/Drift summary is present with lower-bound count 487 and aggregate item count 45.
- Safe Action tiers are present: `T0`, `T0i`, `T1`, `T2`, `T3`, `T4`, `T5`, `T6`, `TX`, `TU`.
- `T4` remains blocked.
- `TX` and `TU` remain non-executable.
- Claude Design remains blocked.

## Remaining Blockers

- Remote-mutation policy is missing.
- Claude Design final screens remain blocked.
- UNKNOWN inventory classes remain unresolved.
- Per-row inventory data is unavailable in accepted artifacts.
- Root authority docs/schema gaps remain: root `RULES.md`, `TRUTH_*.md`, `SYSTEM_*.md`, and dopetask canonical schema were not found.
- Runtime `dopemux help` resolution remains an accepted residual `UNKNOWN`; live runtime discovery was out of scope.
