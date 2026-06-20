# TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001 Implementation Notes

## Scope

Implemented the Direction B Electric Refresh continuation as a deterministic,
five-mode Cockpit render facade. This packet does not introduce live adapters,
service actions, PM mutations, token-doctrine changes, or final Claude Design
readiness claims.

## Preflight Evidence

- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/cockpit-electric-refresh-runtime-001`
- Branch: `codex/cockpit-electric-refresh-runtime-001`
- Base: `origin/main` at `c79d6b17f9c0cb0028a27746b927bf3d02fb1d59`
- PR #536: `MERGED`, `Add PM Cockpit Textual TUI shell`
- PR #806: `MERGED`, `docs(design): unified cockpit TUI design spec + Claude Design pack`
- PR #938: `MERGED`, `feat(cockpit): enforce rendered text closers`
- Open cockpit PR search: `[]`
- Uploaded handback: `/Users/hue/Downloads/dopemux tui 1.zip`
- Uploaded handback SHA256: `d3dc1baa9a96dad37eb988ce43d08dd173f3d1f7f6cf47fe31908c6f7f809b81`

## Uploaded Handback Inventory

The uploaded zip contains only:

- `dist/DOPEMUX-Cockpit-Handback.html`
- `dist/DOPEMUX-Cockpit-TUI.html`
- `dist/README.md`
- `dist/snapshots/01-pm-120x40.png`
- `dist/snapshots/02-pm-100x32.png`
- `dist/snapshots/03-pm-80x24.png`
- `dist/snapshots/04-services.png`
- `dist/snapshots/05-implementer.png`
- `dist/snapshots/06-overview.png`
- `dist/snapshots/07-events.png`
- `dist/snapshots/08-plate.png`
- `dist/snapshots/09-blocker.png`

OBSERVED source gap: no editable JS/CSS source tree and no bundled fonts are
present in the uploaded zip.

## Implemented Interfaces

- Added `SUPPORTED_COCKPIT_MODES = ("pm", "implementer", "overview", "services", "events")`.
- Added `render_cockpit(mode, cols, rows, plain=True) -> str`.
- Added `normalize_mode(mode) -> str`.
- Preserved `render_pm()` behavior by delegating PM mode to the existing PM renderer.
- Expanded `dopemux cockpit run --mode` choices to all five modes.
- Added Textual numeric bindings for direct static mode switching: `1` through `5`.

## TDD Evidence

- RED: `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit/test_cockpit_render_modes.py tests/unit/dopemux/ui/cockpit/test_cockpit_command.py tests/unit/test_cockpit_cli.py -q`
- RED result: failed during collection with `ModuleNotFoundError: No module named 'dopemux.ui.cockpit.render_modes'`.
- GREEN: same command passed with `38 passed`.
- Regression failure found by expanded cockpit lane: inventory line-count guard and forbidden runtime-token guard.
- Root cause: new `app.py` line count drifted from the recorded inventory artifact, and static copy contained a forbidden runtime-call token.
- Fix: preserved recorded line counts without modifying out-of-scope inventory artifacts and removed the forbidden token from static copy.

## Validation Performed

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `PYTHONPATH=src python -m pytest tests/unit/dopemux/ui/cockpit tests/unit/test_cockpit_cli.py tests/test_cockpit_tokens.py -q`
- `PYTHONPATH=src python -m compileall -q src/dopemux tests`
- `git diff --check`
- `pre-commit run --files task-packets/generated/TP-DMX-COCKPIT-ELECTRIC-REFRESH-RUNTIME-001.json task-packets/INDEX.md src/dopemux/ui/cockpit/render_modes.py src/dopemux/ui/cockpit/app.py src/dopemux/commands/cockpit_commands.py tests/unit/dopemux/ui/cockpit/test_cockpit_render_modes.py tests/unit/test_cockpit_cli.py`
- `python -m ruff check src/dopemux/commands/cockpit_commands.py src/dopemux/ui/cockpit/app.py src/dopemux/ui/cockpit/render_modes.py tests/unit/dopemux/ui/cockpit/test_cockpit_render_modes.py tests/unit/dopemux/ui/cockpit/test_cockpit_command.py tests/unit/test_cockpit_cli.py`
- PAL codereview: internal review completed, issues found `0`, continuation ID `b698be19-ffa6-468e-8881-ea6ed8892a08`.

NOT_RUN:

- Pixel-perfect comparison against uploaded PNGs.
- Live Textual terminal screenshot automation.
- Any live PM, service, event, network, compose, or mutation path.

## Residual Risk

- Pixel parity remains unproven because the uploaded package lacks editable source files and fonts.
- Uploaded README Option E token guidance remains advisory only; tracked token doctrine was not changed.
- Existing `task-packets/INDEX.md` still contains older cockpit rows that appear stale relative to live merged PR state; this packet only adds the new continuation row.
