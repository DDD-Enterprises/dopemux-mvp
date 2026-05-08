# LANDED_WORK_MATRIX — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

Definitions:
- `LANDED_ON_MAIN`: artifact / commit reachable from `origin/main` HEAD.
- `LANDED_ON_PACK_ONLY`: reachable from `origin/pack/cockpit-pack-remediate-006-ia` but **not** from `origin/main`.
- `NOT_PRESENT_ON_MAIN`: artifact missing from `origin/main` and may exist only on a PR head branch.
- `NOT_PRESENT`: not authored on either branch (referenced but not yet drafted).

## Per-packet matrix

| Packet ID | Expected role | Expected PR | landed_status | open_pr_status | Open PR refs |
| --- | --- | --- | --- | --- | --- |
| TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA | Parent series anchor | n/a (series) | LANDED_ON_PACK_ONLY | OPEN_STACKED | #572, #573 |
| TP-DMX-COCKPIT-RUNTIME-RENDER-001 | Wire runtime renderer | #568 | LANDED_ON_PACK_ONLY | NO_OPEN_PR | — |
| TP-DMX-COCKPIT-SETTINGS-RUNTIME-001 | Wire settings runtime | #569 | LANDED_ON_PACK_ONLY | NO_OPEN_PR | — |
| TP-DMX-COCKPIT-UNKNOWN-DRIFT-001 | Wire unknown drift queue | #570 | LANDED_ON_PACK_ONLY | NO_OPEN_PR | — |
| TP-DMX-COCKPIT-INVENTORY-REGEN-001 | Regenerate current head inventory | #571 | LANDED_ON_PACK_ONLY | NO_OPEN_PR | — |
| TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001 | Audit stack readiness | #572 | NOT_PRESENT_ON_MAIN | OPEN_STACKED | #572 |
| TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001 | Repair runtime contract gaps | #573 | NOT_PRESENT_ON_MAIN | OPEN_RELEVANT | #573 |
| TP-DMX-COCKPIT-MERGE-EXECUTE-001 | Operator-authorized consolidation | n/a | NOT_PRESENT | NO_OPEN_PR | — |
| TP-DMX-COCKPIT-MAIN-STATE-RECON-001 | This packet | n/a | NOT_PRESENT_ON_MAIN | NO_OPEN_PR | — |

## Observed file surface comparison

### `origin/main` HEAD (`d52fbf1b8`)

- `src/dopemux/ui/cockpit/`: `__init__.py`, `app.py`, `render.py`. **No** `runtime_contract.py`.
- `tests/unit/dopemux/ui/cockpit/`: `__init__.py`, `test_cockpit_command.py`, `test_cockpit_render.py`. **No** `test_runtime_contract.py`, **no** `test_inventory_regen_artifacts.py`, **no** `tests/unit/test_cockpit_cli.py`.
- `out/cockpit-*` directories: **none**.
- `proof/cockpit-*`: only the legacy file `proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json` (predates this pack series).
- `task-packets/generated/`: **directory does not exist**.

### `origin/pack/cockpit-pack-remediate-006-ia` HEAD (`b173efd83`)

- `src/dopemux/ui/cockpit/`: `__init__.py`, `app.py`, `render.py`, **plus** `runtime_contract.py` (first added in commit `ea640b47b` as part of PR 568, modified again in PR 569 and PR 570).
- `tests/unit/dopemux/ui/cockpit/`: includes `test_runtime_contract.py` and `test_inventory_regen_artifacts.py`.
- `tests/unit/test_cockpit_cli.py`: present.
- `out/cockpit-*` directories: `cockpit-command-palette`, `cockpit-ia-reconcile`, `cockpit-inventory-regen`, `cockpit-pack-remediation`, `cockpit-runtime-render`, `cockpit-safe-actions`, `cockpit-settings-runtime`, `cockpit-unknown-drift`.
- `proof/cockpit-*` directories: `cockpit-inventory-regen`, `cockpit-runtime-render`, `cockpit-settings-runtime`, `cockpit-unknown-drift`.
- `task-packets/generated/`: contains `TP-DMX-COCKPIT-INVENTORY-REGEN-001.json`, `TP-DMX-COCKPIT-RUNTIME-RENDER-001.json`, `TP-DMX-COCKPIT-SETTINGS-RUNTIME-001.json`, `TP-DMX-COCKPIT-UNKNOWN-DRIFT-001.json`.

## Containment evidence

```
ancestry-probe(merge-base --is-ancestor) 39ad991f72dd58b22944146a38649ac1b0de04fc origin/main           => NO
ancestry-probe(merge-base --is-ancestor) 39ad991f72dd58b22944146a38649ac1b0de04fc origin/pack/cockpit-pack-remediate-006-ia => YES
ancestry-probe(merge-base --is-ancestor) a4ca22da678f0578895eb237ac270041811d80d4 origin/main           => NO
ancestry-probe(merge-base --is-ancestor) a4ca22da678f0578895eb237ac270041811d80d4 origin/pack/...006-ia => YES
ancestry-probe(merge-base --is-ancestor) 7ff3ea44e31749ce75e653b81790ab6eba3ae65e origin/main           => NO
ancestry-probe(merge-base --is-ancestor) 7ff3ea44e31749ce75e653b81790ab6eba3ae65e origin/pack/...006-ia => YES
ancestry-probe(merge-base --is-ancestor) b173efd83c871c30f2bd86530921c866d08e7e45 origin/main           => NO
ancestry-probe(merge-base --is-ancestor) b173efd83c871c30f2bd86530921c866d08e7e45 origin/pack/...006-ia => YES (= pack HEAD)
```

## Drift items surfaced by this matrix

1. The four merged Cockpit feature PRs (568–571) live entirely on the pack branch. **None of their work landed on `origin/main`**. Treat the 196-file diff between main and pack as the unmerged Cockpit remediation surface.
2. Two open Cockpit PRs (#572 stack-consolidation artifact, #573 runtime-contract repair) target the pack branch. Both are not yet merged.
3. PR #572 documents readiness for #568–#571 only; it does **not** audit PR #573. Any operator-initiated consolidation that ignores this gap will land an unaudited runtime surface.
4. `TP-DMX-COCKPIT-MERGE-EXECUTE-001` is referenced under `depends_on` but no authored TP JSON exists on either branch. It is a referenced future packet, not a stale or missing landed packet.
