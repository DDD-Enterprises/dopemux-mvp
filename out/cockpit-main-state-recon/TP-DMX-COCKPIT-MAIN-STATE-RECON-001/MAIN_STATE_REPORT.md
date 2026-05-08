# MAIN_STATE_REPORT — TP-DMX-COCKPIT-MAIN-STATE-RECON-001

As of 2026-05-07.

## Branch heads

- `origin/main` HEAD: `d52fbf1b8786b27305afb6c52ac294ba7a12f2d5` — `fix(extraction): preserve lexical BM25 matches`.
- `origin/pack/cockpit-pack-remediate-006-ia` HEAD: `b173efd83c871c30f2bd86530921c866d08e7e45` — `docs(cockpit): regenerate current head inventory (#571)`.
- Pack vs main: ahead 18 / behind 9; 196 files differ.

## OBSERVED — main carries no Cockpit pack remediation work

- Cockpit `src` on main: only `__init__.py`, `app.py`, `render.py`. No `runtime_contract.py`.
- Cockpit `tests` on main: only `__init__.py`, `test_cockpit_command.py`, `test_cockpit_render.py`. No `test_runtime_contract.py`, `test_inventory_regen_artifacts.py`, or `tests/unit/test_cockpit_cli.py`.
- `out/cockpit-*` on main: **none**.
- `proof/cockpit-*` on main: only the legacy file `proof/cockpit-pm-implementer-processing-pack-2026-04-24.proof.json` (predates this pack series).
- `task-packets/generated/` directory does **not exist** on main.

## OBSERVED — pack carries the full Cockpit remediation surface

- Cockpit `src` on pack: same three files plus `runtime_contract.py` (first added by commit `ea640b47b`, part of PR 568; further modified in PR 569 and PR 570).
- Cockpit `tests` on pack: includes `test_runtime_contract.py`, `test_inventory_regen_artifacts.py`, and `tests/unit/test_cockpit_cli.py`.
- `out/cockpit-*` on pack: 8 directories — `command-palette`, `ia-reconcile`, `inventory-regen`, `pack-remediation`, `runtime-render`, `safe-actions`, `settings-runtime`, `unknown-drift`.
- `proof/cockpit-*` on pack: 4 directories — `inventory-regen`, `runtime-render`, `settings-runtime`, `unknown-drift`.
- `task-packets/generated/` on pack: 4 packet JSONs — INVENTORY-REGEN-001, RUNTIME-RENDER-001, SETTINGS-RUNTIME-001, UNKNOWN-DRIFT-001.

## OBSERVED — open PRs

- Cockpit-relevant: **#572** (stack consolidation artifact, OPEN_STACKED), **#573** (runtime contract fidelity, OPEN_RELEVANT).
- Cockpit-unrelated: **#582** (dependabot pip), **#583** (dependabot uv), **#584** (PR576 review follow-ups, MCP CLI only).

## INFERRED

- No pack-to-main merge has been authored: no commit on `origin/main` contains any of the four cockpit feature merge commits.
- `origin/main` carries only the pre-pack Cockpit surface. Anything Cockpit-flavored in current `main` is not part of the pack remediation series.
- PR 572 self-reports verdict `READY_WITH_RISKS_NEEDS_LEDGER_DECISION` for PRs 568–571, but its consolidation artifact does not audit PR 573 (no cross-reference between the two open PRs). Treat the verdict as scoped to 568–571 only.

## UNKNOWN

- Review decisions for PRs 572 and 573: empty in the API response; whether human reviews are pending or absent is not asserted by this packet.
- Ledger acceptance/rejection state for the residual risks PR 572 flagged (Settings/Admin per-row tier mapping, remote-mutation policy, inventory `current_head` drift, root authority/schema gap): not visible in main artifacts.
- Authored `TP-DMX-COCKPIT-MERGE-EXECUTE-001` packet JSON: not present on either branch; classified `NOT_PRESENT`, not `UNKNOWN`.

## CONFLICTING

None observed in this audit.

## Governance state preserved

- `safe_for_claude_design`: `NO`.
- `READY_FOR_CLAUDE_DESIGN`: `not approved`.
- No Claude Design upload performed.
- No T4 remote mutation performed.
- No canonical writes performed.
- No runtime action execution performed.
- No runtime reclassification performed.
- Unknown / Drift Queue remains non-executing per parent series boundaries; TX/TU remain non-executable per PR 573 body.

## Design continuation: not yet ready

`origin/main` is **not** ready for Cockpit design continuation. Reasons:

1. None of the cockpit pack remediation surface is on main.
2. Two open Cockpit PRs are blocking; PR 572's verdict does not cover PR 573.
3. Multiple residual risks remain accepted-but-not-disposed.
4. The operator-initiated consolidation packet (`TP-DMX-COCKPIT-MERGE-EXECUTE-001`) has not been authored.

See `DESIGN_PICKUP_PLAN.md` for the recommended sequencing.
