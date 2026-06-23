# Cockpit Textual Screenshot Automation Research

Packet: `TP-DMX-COCKPIT-TEXTUAL-SCREENSHOT-AUTOMATION-001`

## OBSERVED

- Worktree: `/private/tmp/dopemux-cockpit-textual-screenshot-automation-001r`.
- Branch: `codex/cockpit-textual-screenshot-automation-001r`.
- Base head: `dddb8e0d7911b548384d94f2aa3fb6d46b2f9504`.
- Current Cockpit Textual runtime path: `src/dopemux/ui/cockpit/app.py`.
- Current five-mode render facade: `src/dopemux/ui/cockpit/render_modes.py`.
- Existing pixel proof generator `scripts/cockpit_pixel_parity_proof.py` exports Textual SVGs as part of pixel-parity proof at `120x40`.
- Historical QA script `qa/scenarios/90_tui_renders.sh` targets older `dopemux.tui.app` / `dopemux.app` paths and is not the current Cockpit runtime authority.
- `CockpitApp.run_test(size=(80, 24))` can export non-empty SVG at the minimum supported viewport.
- `rsvg-convert` is optional environmental tooling; missing rasterization must be reported as `UNKNOWN`, not hidden.

## INFERRED

- The next finish-line lane should isolate repeatable current-runtime Textual screenshots instead of re-running pixel parity classification.
- A separate proof script is safer than broadening the pixel parity script because the packet purpose is screenshot automation, not design comparison.
- Raw SVG hashes plus normalized SVG hashes make the proof more replayable across Textual-generated CSS/clip identifier changes.

## UNKNOWN

- Pixel equivalence to uploaded PNG references remains outside this packet.
- Final design approval remains unproven.
- Live PM, service, task-orchestrator, ConPort, and dope-memory integration are not exercised.
- Cross-platform font and terminal raster equivalence are not proven.
- Independent Claude Code, Grok Build, and agy audits depend on local auth/runtime availability.

## TRACE

1. `CockpitApp(mode, cols, rows)` constructs the current Textual app.
2. `CockpitApp.run_test(size=(cols, rows))` runs headless.
3. `app.export_screenshot()` returns SVG for that mode and viewport.
4. `render_cockpit(mode, cols, rows, plain=True)` writes matching deterministic text render proof.
5. Optional `rsvg-convert` rasterization writes PNG proof when available.

## CHALLENGE

- Missing mode/viewport/hash metadata would make artifacts weak evidence.
- Silent skips would create false proof.
- Treating missing `rsvg-convert` as a hard failure would make proof depend on optional local tooling.
- Any design, token, NO_COLOR, glyph, PM, or live integration change would exceed scope.
