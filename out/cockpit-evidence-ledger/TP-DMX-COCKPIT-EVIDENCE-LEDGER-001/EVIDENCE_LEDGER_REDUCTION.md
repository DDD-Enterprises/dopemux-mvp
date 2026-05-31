# Evidence Ledger Reduction

Packet: `TP-DMX-COCKPIT-EVIDENCE-LEDGER-001`

Current head: `f257f3e6528ed17413fa985e9b44765c59be37f5`

Source ledger: `out/cockpit-ia-reconcile/TP-DMX-COCKPIT-IA-RECONCILE-001/EVIDENCE_LEDGER.md`

## Verdict

Phase 1 condition 8 is satisfied for this packet. The specific open ledger items named by `CLAUDE_DESIGN_BLOCKERS.md` are now either resolved by current authority/runtime evidence or explicitly rejected as current Cockpit command affordances.

This does not flip `safe_for_claude_design`; it remains `NO`.

## Reductions

| Old ledger item | Current status | Evidence |
| --- | --- | --- |
| Root `RULES.md` absent. | RESOLVED | AGENTS.md allows tracked docs/reference equivalents; `docs/03-reference/governance/rules.md` exists. |
| Root `TRUTH_*.md` files absent. | RESOLVED | AGENTS.md explicitly falls back to `docs/03-reference/truth/*`; seven truth files are present there. |
| Prior inventory generated at an old HEAD. | RESOLVED | `TP-DMX-COCKPIT-INVENTORY-REGEN-001` merged before this packet; this packet is based on integration head `f257f3e65`. |
| Runtime help remained an input UNKNOWN. | RESOLVED | `PYTHONPATH=src python -m dopemux --help` exits 0 and renders current command help. |
| Decision subcommands unresolved. | EXPLICITLY_REJECTED | Runtime registers only `decisions` with `energy` and `patterns` groups; source records no concrete decision-management callbacks. |
| Optional `genetic` unresolved. | EXPLICITLY_REJECTED | No current top-level `genetic` command is registered; no active `services/genetic_agent` directory is present; remaining genetic path is under `SYSTEM_ARCHIVE`. |
| Defined-but-not-registered `worktree`/`vault` surfaces unresolved. | EXPLICITLY_REJECTED | Runtime registers neither `worktree`, `worktrees`, nor `vault`; source-defined groups are not current runtime command affordances. |

## Runtime CLI Snapshot

Observed with `PYTHONPATH=src python - <<'PY' ... from dopemux.cli import cli ... PY`:

| Command | Registered |
| --- | --- |
| `decisions` | true |
| `genetic` | false |
| `worktree` | false |
| `worktrees` | false |
| `vault` | false |
| `env` | true |
| `session` | true |
| `safe` | true |

`decisions` subcommands: `energy`, `patterns`.

The import emitted nonfatal LiteLLM botocore preload warnings. The registration probe and help command both exited 0.

## Boundary

- No runtime code changed.
- No command was registered or removed.
- No Cockpit row was reclassified.
- No action execution path was added.
- No final-screen readiness is claimed.
- Gate flip remains owned by `TP-DMX-COCKPIT-GATE-FLIP-001`.
