# 02 — Planner · TP-DMX-ORCH-CS-P1

## Deliverables
1. `docs/03-reference/systems/task-orchestrator/callable-surface-inventory.md` — prose
   inventory (tool classification table, command→surface mapping, read-surface boundary,
   provenance/skew notes), following the serena/conport precedent.
2. `.taskorchestrator/surface_manifest.json` — independent machine-readable authority:
   per-tool classification + per-command `{surface_class, orchestrator_tools}`. Hand-authored,
   NOT generated from frontmatter (so drift is detectable against an external contract).
3. `scripts/validate_dx_surface.py` — read-only validator. Fails if a read command lists a
   write tool, a command lists an unknown tool, or frontmatter drifts from the manifest.
   Exposes `run_validation(root)` for in-process testing.
4. `tests/orchestrator/test_dx_surface_manifest.py` — pytest: manifest validity, internal
   consistency, validator passes on the committed surface, read commands ⊆ read-only tools,
   every file catalogued, and a **bite test** (tampered read command must fail).
5. `task-packets/TP-DMX-ORCH-CS-P1.json` — canonical packet.
6. `proof/TP-DMX-ORCH-CS-P1/` — this proof bundle + PAL artifacts.

## Sequencing
manifest → validator → run validator (happy + bite) → test → inventory doc → packet → verify
suite → proof bundle → commit → PR.

## Boundary
Validator/test are runtime-read-only (file inspection only) → within P1's no-writes /
no-execution / no-bridge / no-memory boundary. No edits to existing commands, config, or ADRs.

## Base / branch
Fresh branch `claude/dmx-orch-cs-p1` off `origin/main` (`59b309f27`). Not on the DCP branch.

## Blast radius
Additive only: 5 new files (+ proof bundle). No existing file modified. `tests/orchestrator/`
already exists (plan's "new dir" assumption was wrong — corrected; only the test file is new).
