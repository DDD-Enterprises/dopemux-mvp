# Evidence Ledger

## Commands Run

- `cd /Users/hue/code/dopemux-mvp && git fetch origin --prune`
- `git worktree add --detach /tmp/dopemux-cockpit-ia-reconcile-20260502-021046 origin/main`
- `pwd`
- `git rev-parse --show-toplevel`
- `git status --short --branch`
- `git branch --show-current`
- `git log --oneline -5`
- `git remote -v`
- `test -e .dopetaskroot && echo "OK .dopetaskroot" || echo "FAIL .dopetaskroot missing"`
- Prior artifact existence checks under `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001`
- Prior inventory JSON count extraction
- Authority/cockpit `rg`, `sed`, `find`, and `ls` inspections
- Artifact generation script for this packet

## Files Inspected

- `AGENTS.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/truth/truth-scope.md`
- `docs/03-reference/truth/truth-systems.md`
- `docs/03-reference/truth/truth-interfaces.md`
- `docs/03-reference/truth/truth-canonicals.md`
- `docs/03-reference/truth/truth-gaps.md`
- `docs/03-reference/systems/dopemux/system-dopemux.md`
- `docs/03-reference/systems/dopetask/system-dopetask.md`
- `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md`
- `docs/03-reference/systems/conport/system-conport.md`
- `docs/03-reference/systems/dope-memory/system-dopememory.md`
- `docs/03-reference/systems/dope-context/system-dopecontext.md`
- `docs/03-reference/systems/dopecon-bridge/system-dopeconbridge.md`
- `docs/03-reference/systems/adhd-engine/system-adhdengine.md`
- `docs/03-reference/systems/repo-truth-extractor/system-repotruthextractor.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/readme.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/review-pack.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/ARCHITECTURE_SAFETY_OVERLAY.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/PM_IMPLEMENTER_COCKPIT_REDIRECTION.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits/cockpit/seed.js`
- `docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits/cockpit/Cockpit.jsx`
- `docs/03-reference/Dopemux Cockpit TUI Design System/ui_kits/cockpit/readme.md`

## Prior Artifacts Used

- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/COMMAND_INVENTORY.md`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/COMMAND_INVENTORY.json`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/COCKPIT_COVERAGE_MATRIX.md`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/COCKPIT_COVERAGE_MATRIX.json`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/IA_GAP_ANALYSIS.md`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/AUTHORITY_ACTION_TAXONOMY.md`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/EVIDENCE_LEDGER.md`
- `/Users/hue/.codex/worktrees/7f12/dopemux-mvp/out/cockpit-command-inventory/TP-DMX-COCKPIT-COMMAND-INVENTORY-001/PROOF.json`

## Missing Files

- `RULES.md`
- root `TRUTH_SCOPE.md`
- root `TRUTH_SYSTEMS.md`
- root `TRUTH_INTERFACES.md`
- root `TRUTH_CANONICALS.md`
- root `TRUTH_GAPS.md`

## Unresolved UNKNOWNs

- Root RULES.md is absent in the fresh worktree; docs/reference rules and AGENTS.md were used where available.
- Root TRUTH_*.md files are absent; docs/03-reference/truth equivalents were used.
- Prior command inventory was generated at old HEAD af5c4627 while this fresh worktree is origin/main 4959a089f; no new command inventory was regenerated in this packet.
- Runtime dopemux help remained an input UNKNOWN from the inventory packet because its environment lacked litellm.
- Decision subcommands, optional genetic, and defined-but-not-registered worktree/vault surfaces remain unresolved until runtime registration is repaired or rejected.
- Final runtime renderer, browser visual approval, screenshot approval, and proof JSON validation for Cockpit remain outside this packet.

## Validation Commands

Validation commands are listed in `PROOF.json` and should be run after artifact generation.
