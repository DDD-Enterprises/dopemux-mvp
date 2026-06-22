# TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001 Research

## Scope

OBSERVED: The user corrected the Cockpit TUI design pack status to continuation input with runtime representation. The next packet must not rebuild Cockpit and should close proof, fidelity, and integration gaps only.

PROPOSED: Make this packet artifact/test-only. It should compare current Cockpit runtime render output against uploaded PNG references and classify deviations as MATCH, ACCEPTABLE_DELTA, DESIGN_DRIFT, RUNTIME_BUG, SPEC_AMBIGUITY, or UNKNOWN. It should not silently fix design drift.

## Evidence Summary

- OBSERVED: Current checkout is `/Users/hue/.codex/worktrees/a6bb/dopemux-mvp` with repo root equal to that path.
- OBSERVED: `origin/main` and local HEAD both resolve to `db3eb365ea0116aa36cf80efbf4cbbbd61eb4b57`.
- OBSERVED: PR #948 is merged with title `feat(cockpit): render electric refresh modes`; merge commit is `db3eb365ea0116aa36cf80efbf4cbbbd61eb4b57`; head ref was `codex/cockpit-electric-refresh-runtime-001`.
- OBSERVED: `task-packets/generated/TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001.json` exists and describes a continuation/remediation packet, not a new Cockpit series.
- OBSERVED: `src/dopemux/ui/cockpit/render_modes.py` exposes `SUPPORTED_COCKPIT_MODES = ("pm", "implementer", "overview", "services", "events")` and a deterministic no-write `render_cockpit(...)` facade.
- OBSERVED: `src/dopemux/ui/cockpit/app.py` provides `CockpitApp` and `run_cockpit(...)`; plain/audit paths return deterministic text, interactive mode launches Textual.
- OBSERVED: `qa/scenarios/90_tui_renders.sh` contains a Textual `export_screenshot()` path, but it targets older `dopemux.tui.app` / `dopemux.app` imports rather than `dopemux.ui.cockpit.app.CockpitApp`.
- OBSERVED: Textual is importable in this environment as version `8.2.7`.
- OBSERVED: Pillow is importable in this environment as version `12.2.0`.
- OBSERVED: Uploaded PNG references under `docs/03-reference/Dopemux Cockpit TUI Design System/uploads/` are:
  - `Screenshot 2026-04-24 at 10.11.21 PM.png`, `1072x739`, `RGBA`.
  - `Screenshot 2026-04-24 at 10.11.37 PM.png`, `1073x738`, `RGBA`.
  - `Screenshot 2026-04-24 at 10.12.47 PM.png`, `1074x752`, `RGBA`.
  - `Screenshot 2026-04-24 at 9.05.48 PM.png`, `412x606`, `RGBA`.
- OBSERVED: Visual inspection shows the three larger PNGs are dark Cockpit/RTE-style surfaces. The `9.05.48 PM` PNG is a light setup form and is not visibly a Cockpit runtime render.
- OBSERVED: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` is present and constrains generated Task Packet JSON fields.
- OBSERVED: `task-packets/INDEX.md` already lists `TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001` as an active UI Cockpit continuation entry.

## Relevant Files

- `AGENTS.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `task-packets/generated/TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001.json`
- `task-packets/INDEX.md`
- `src/dopemux/ui/cockpit/render.py`
- `src/dopemux/ui/cockpit/render_modes.py`
- `src/dopemux/ui/cockpit/app.py`
- `tests/unit/dopemux/ui/cockpit/test_cockpit_render.py`
- `tests/unit/dopemux/ui/cockpit/test_cockpit_render_modes.py`
- `tests/unit/dopemux/ui/cockpit/test_cockpit_command.py`
- `tests/unit/test_cockpit_cli.py`
- `tests/test_cockpit_tokens.py`
- `qa/scenarios/90_tui_renders.sh`
- `docs/03-reference/Dopemux Cockpit TUI Design System/uploads/*.png`

## Risks

- DESIGN_DRIFT risk: Current runtime is a deterministic artifact-derived Textual/static surface, while uploaded references appear to show an older RTE cockpit design with left rail, dense table rows, toolbar chips, and richer visual chrome.
- SPEC_AMBIGUITY risk: The uploaded PNG set includes at least one setup-form screenshot that does not appear to be a runtime Cockpit surface.
- TOOLING risk: Existing `qa/scenarios/90_tui_renders.sh` exports a Textual SVG from older import paths and may not prove Cockpit runtime screenshot parity.
- PIXEL-PARITY risk: Textual `export_screenshot()` produces SVG; uploaded references are PNG. A faithful pixel comparison needs deterministic rasterization, viewport mapping, font handling, and threshold definitions. Without those, the comparison should classify UNKNOWN rather than claiming MATCH.
- AUTHORITY risk: Uploaded design artifacts are reference inputs, not runtime truth. Runtime/source truth controls behavior claims.
- SCOPE risk: If drift is found, this packet should report it and not edit runtime UI design unless a separate implementation packet is authorized.

## Candidate Verification Commands

```bash
python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit tests/unit/test_cockpit_cli.py tests/test_cockpit_tokens.py -q
PYTHONPATH=src python -m compileall -q src/dopemux tests
PYTHONPATH=src python scripts/cockpit_pixel_parity_proof.py --output proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001
python -m json.tool proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/PIXEL_PARITY_REPORT.json >/dev/null
git diff --check
pre-commit run --files task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json task-packets/INDEX.md proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/research.md
```

## Research Conclusion

PROPOSED: Proceed with `TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001` as an artifact/test-only continuation packet. The first implementation slice should create the packet and a proof report generator or deterministic proof artifacts. The comparison must classify the three dark uploaded references separately from the setup-form reference, and it must preserve UNKNOWN where raster/font/viewport equivalence is not proven.

<workflow-checkpoint phase="research" status="complete" task="TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001" summary="Research captured for Cockpit pixel parity proof packet" artifact="/Users/hue/.codex/worktrees/a6bb/dopemux-mvp/proof/cockpit-pixel-parity-proof/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001/research.md" verification="python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-PIXEL-PARITY-PROOF-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json;;PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit tests/unit/test_cockpit_cli.py tests/test_cockpit_tokens.py -q" />
