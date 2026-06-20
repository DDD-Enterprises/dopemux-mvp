# Prompt 6 Bundle — Manifest (current main)

**Bound to:** `origin/main` @ `817d9d2275cd83d5fc0385828f64f46db2016523`
**Assembled:** 2026-06-17 · **Subject:** DCP execution-gating chain (#904 → #906 → 0006 hardening → #923)
**Purpose:** Hand GPT-5.5 Pro everything needed to run the Prompt 6 implementation audit of the DCP lane engine on current main. No 0005 rerun; the lane engine is implemented, merged, and post-merge-hardened.

## Merged PR chain (all on main `817d9d227`)

| PR | Merge SHA | Role |
|----|-----------|------|
| [#902](https://github.com/DDD-Enterprises/dopemux-mvp/pull/902) | `a740edc40e67` | 0002R — lock 5 routing-classifier invariants (tests only) |
| [#904](https://github.com/DDD-Enterprises/dopemux-mvp/pull/904) | `ba36b58cb7a1` | Precedence fix — hard-BLOCKED before UNKNOWN-authority guard |
| [#906](https://github.com/DDD-Enterprises/dopemux-mvp/pull/906) | `02fa9b30ac0a` | 0005 lane engine MVP — `decide_lane()` pure consumer |
| [#908](https://github.com/DDD-Enterprises/dopemux-mvp/pull/908) | `12b3793fe394` | 0006 classifier provenance-hardening packet (docs) |
| [#909](https://github.com/DDD-Enterprises/dopemux-mvp/pull/909) | `0c521642c0e5` | 0007 trusted input-provenance contract (docs) |
| [#923](https://github.com/DDD-Enterprises/dopemux-mvp/pull/923) | `817d9d2275cd` | Post-merge fail-closed hardening (closes #906 threads F1/F2) |

**0006 implementation** (not just the docs packet) landed on main in `b460047eb` + 4 CLI provenance fixes (`d14dbda80`, `5c7663c0a`, `ea4871e0f`, `556ffff1b`).

## Runtime files to audit (current main)

| File | Role |
|------|------|
| `src/dopemux/dcp/lane_engine.py` | `decide_lane()` pure consumer (post-#923) |
| `src/dopemux/dcp/lane_model.py` | `LaneDecision` / `LaneKind` frozen data |
| `src/dopemux/dcp/routing_classifier.py` | classifier + 0006 provenance hardening (authoritative gate) |
| `src/dopemux/dcp/routing_model.py` | `RouteDecision`, `is_runnable()`, `from_dict` |
| `src/dopemux/dcp/routing_backend_policy.py` | inert sibling consumer (`select_backend_policy`) |
| `src/dopemux/commands/dcp_commands.py` | read-only CLI projection (`classify`, `recommend-backend`) |
| `tests/unit/dcp/test_lane_engine.py` | lane-engine tests (+2 regressions from #923) |
| `tests/unit/dcp/test_routing_classifier.py` | classifier + provenance tests |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005.md` | 0005 packet |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0005-POSTMERGE-FIX.json` | #923 canonical packet |
| `task-packets/DMX-DCP-MODEL-ROUTING-MVP-0006.json` / `0007.json` | provenance packets |

## Bundle attachments (this directory + sibling)

- `MANIFEST.md` (this file)
- `GO_NO_GO.md` — readiness verdict bound to `817d9d227`
- `RISK_LEDGER.md` — UNKNOWNs / residual risk
- `COMMAND_LOG.md` — verification commands + exit codes
- `../pr906_postmerge_triage/CURRENT_MAIN_DCP_AUDIT.md` — full execution-gating audit + thread classification
- `../pr906_postmerge_triage/PR906_TRIAGE.md` / `.json` — #906 thread triage
- `../pr906_postmerge_triage/COMMAND_LOG.md` — triage command log

## What Prompt 6 should NOT re-review
Prompt 5 architecture, PR #873 (evidence lane), runner/connector wrappers, Secure-MCP-facade impl, live-write impl, ECC intake impl, cockpit, unrelated coldstart/RTE work.
