# DESIGN_PICKUP_STATE

Packet: `TP-DMX-COCKPIT-DESIGN-PICKUP-001`

safe_for_claude_design: NO
READY_FOR_CLAUDE_DESIGN: not approved

## Verdict

`READY_FOR_DESIGN_DISCUSSION`

Design discussion can resume from `origin/main` at `e4f01cb176fe0d9f6a1dac410598b04985b92b2c`. Primitive-level sketching, IA critique, component inventory review, flow descriptions, state diagrams, and design-input briefs are acceptable discussion artifacts.

Final Claude Design screens remain blocked.

## Observed On Main

- OBSERVED: `origin/main` contains pack-to-main merge commit `0ca8fae9dee59bc410cf013cc9af741aa28b88e7` from PR #587.
- OBSERVED: PR #573 is merged and included through the pack-to-main merge.
- OBSERVED: `src/dopemux/ui/cockpit/runtime_contract.py` exists on main.
- OBSERVED: focused Cockpit tests exist under `tests/unit/dopemux/ui/cockpit` plus `tests/unit/test_cockpit_cli.py`.
- OBSERVED: durable Cockpit artifact trees exist under `out/cockpit-*` for the pack, runtime render, Settings/Admin, Unknown/Drift, inventory, safe actions, palette, IA reconcile, and runtime-contract fidelity.

## Runtime Snapshot Evidence

OBSERVED from `PYTHONPATH=src python` runtime snapshot probe:

- `safe_for_claude_design`: `NO`
- `READY_FOR_CLAUDE_DESIGN`: `not approved`
- top-level modes: PM, Implementer, Overview, Services, Events
- global surfaces: Command Palette, Settings/Admin/Runtime, Safe Actions / Proof Gate, Unknown / Drift Queue
- Settings/Admin unknown tier count: 62
- Unknown/Drift lower-bound queue items: 487
- Unknown/Drift action execution: blocked
- runtime reclassification: blocked

## Conflicting Or Stale Evidence

- CONFLICTING: PR #585's design pickup plan says nothing from the pack landed on `origin/main`; that was true when authored, but is false after PR #587 merged on 2026-05-07.
- OBSERVED: PR #572 remains open against `main`; GitHub pulls API reports `mergeable=false` and `mergeable_state=dirty`.
- OBSERVED: the pack-to-main proof bundle exists only in the retained local worktree and is not present on `main`.

## Unknowns

- UNKNOWN: whether Ledger has accepted the local-only pack-to-main proof bundle as durable.
- UNKNOWN: whether PR #572 should be closed, superseded, retargeted, or replaced.
- UNKNOWN: exact per-row Settings/Admin gate tiers for the 62 rows.
- UNKNOWN: exact row-level breakdown behind several Unknown/Drift aggregate classes.
- UNKNOWN: root `RULES.md`, root `TRUTH_*.md`, and root `SYSTEM_*.md` remain absent; tracked equivalents exist under `docs/03-reference/`.

## Design Status

- Design discussion: allowed.
- Primitive-level sketches: allowed as non-final discussion artifacts.
- Final-screen design: blocked.
- Claude Design upload: forbidden.
- Runtime action execution: not authorized.
- T4 remote mutation: blocked.
- Canonical writes: not authorized.
- Merge/proof governance mutation: not authorized by this packet.
