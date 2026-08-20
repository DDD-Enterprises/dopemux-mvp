# R4 Scope Freeze

## Frozen source

`proof/TP-DMX-PR-PREP-SPECIALIST-V2-001/LEGACY_SEMANTICS_SCAN_R3.md`
SHA256: `f5cbac0bbffd19e5c04a25fc7bb817b2ffa464e9f5463f7dedc00ef9320d575a`

## Frozen 19-path ACTIVE_CONTRADICTION set

Extracted, sorted, verified to exist. See `R4_ACTIVE_CONTRADICTION_PATHS.txt` (19 lines).

`ACTIVE_CONTRADICTION_COUNT=19` — matches supervisor-required count. R4 proceeds.

## Envelope-only paths (candidate 21 minus frozen 19 = 2)

The R4 candidate transport envelope adds 21 adapter/state-model paths to the
allowlist. Two are not in the frozen 19 and must remain byte-unchanged for
the rest of R4:

| Path | Baseline SHA256 |
|---|---|
| `docs/03-reference/pr-pipeline/prep/adapters/vibe/readme.md` | `7fe055708304b30164c49b09514feefd0179a0994293fc7a8947ca93bd6e7ea7` |
| `docs/pr_prep/adapters/vibe/readme-2.md` | `7fe055708304b30164c49b09514feefd0179a0994293fc7a8947ca93bd6e7ea7` |

These will be re-hashed at the S3 gate to prove byte-identity was preserved.
