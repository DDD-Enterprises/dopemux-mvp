# TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001 Plan

## Chosen Approach

Create an artifact/test-only continuation packet. Add a small deterministic proof generator that:

1. Exports current Cockpit Textual SVG screenshots for all five runtime modes through `CockpitApp.run_test(...)`.
2. Records plain text runtime renders for all five modes.
3. Inspects the uploaded PNG references and records dimensions, luminance, and category.
4. Rasterizes exported SVGs when `rsvg-convert` is available and records image metadata.
5. Produces `PIXEL_PARITY_REPORT.json` and `PIXEL_PARITY_REPORT.md` with classifications:
   - `DESIGN_DRIFT` for dark Cockpit/RTE references that do not map to current five-mode Cockpit runtime chrome.
   - `SPEC_AMBIGUITY` for the setup-form PNG.
   - `UNKNOWN` when true pixel equivalence cannot be proven.

This packet must not edit runtime rendering, tokens, docs that claim readiness, or design assets.

## File Targets

- `task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json`
- `task-packets/INDEX.md`
- `scripts/cockpit_pixel_parity_proof.py`
- `tests/unit/dopemux/ui/cockpit/test_pixel_parity_proof.py`
- `proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/research.md`
- `proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/plan.md`
- Generated proof artifacts under `proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/`

## Execution Steps

1. RED: Add focused tests for the proof generator contract.
   - Verify it classifies bright setup-form references as `SPEC_AMBIGUITY`.
   - Verify it classifies dark Cockpit/RTE references as `DESIGN_DRIFT` with residual pixel certainty `UNKNOWN`.
   - Verify it emits all required report classifications and runtime mode artifacts.
   - Command: `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_pixel_parity_proof.py -q`

2. GREEN: Implement `scripts/cockpit_pixel_parity_proof.py`.
   - Use only local files and deterministic runtime render/export paths.
   - Use Pillow and Textual already present in the environment.
   - Treat missing rasterization tools as `UNKNOWN`, not pass.
   - Do not mutate uploaded PNGs or runtime sources.
   - Command: `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_pixel_parity_proof.py -q`

3. Create the generated task packet and index entry.
   - Packet must conform to `dopetask-canonical-spec.json`.
   - Packet allowlist must include only proof packet, index, proof script, focused test, and proof artifacts.
   - Command: `python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`

4. Generate proof artifacts.
   - Command: `PYTHONPATH=src python scripts/cockpit_pixel_parity_proof.py --output proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001`
   - Verify JSON parses: `python -m json.tool proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/PIXEL_PARITY_REPORT.json >/dev/null`

5. Run focused validation and precommit.
   - `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit tests/unit/test_cockpit_cli.py tests/test_cockpit_tokens.py -q`
   - `PYTHONPATH=src python -m compileall -q src/dopemux tests scripts/cockpit_pixel_parity_proof.py`
   - `git diff --check`
   - `pre-commit run --files task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json task-packets/INDEX.md scripts/cockpit_pixel_parity_proof.py tests/unit/dopemux/ui/cockpit/test_pixel_parity_proof.py proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/research.md proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/plan.md`

## Challenge Findings

- Do not call this a `MATCH` proof unless rasterized current runtime and uploaded reference share explicit viewport/font/source equivalence. Current evidence does not prove that.
- Do not classify the setup-form PNG as a runtime failure. It is reference-set ambiguity unless additional source authority maps it to Cockpit.
- Do not "fix" visual drift in this packet. Report design/runtime gaps and leave remediation to a separate packet.
- Do not let the existing `qa/scenarios/90_tui_renders.sh` SVG path stand as Cockpit proof; it targets older imports.
- Do not claim live integration. This packet exercises static render/export only.

<workflow-checkpoint phase="plan" status="complete" task="TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001" summary="Plan drafted for artifact-only pixel parity proof" artifact="/Users/hue/.codex/worktrees/a6bb/dopemux-mvp/proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/plan.md" verification="PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_pixel_parity_proof.py -q" />
