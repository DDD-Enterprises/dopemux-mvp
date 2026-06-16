# DMX-COCKPIT-FONTS-102 Proof Bundle

## Scope

- TP: `DMX-COCKPIT-FONTS-102-patch-flags-editor-proportional-family-name`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/cockpit-fonts-102-patch-flags`
- Branch: `codex/cockpit-fonts-102-patch-flags`
- Base for worktree: `origin/codex/cockpit-fonts-101-rename-plan-keys` at `9165f591011717b80226f84464c276b643e8eaa7`
- Dependency: stacked on PR #912 because packet 102 depends on packet 101 and PR #912 is not merged into `origin/main`.
- Repo marker: `.dopetaskroot` present

## Files Changed

- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/patch-nerd-font.sh`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/test-name-tables.sh`
- `task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-102-patch-flags-editor-proportional-family-name.json`
- `proof/cockpit-fonts-102/proof-bundle.md`

## Evidence

- RED before implementation:
  - `grep -q 'variable-width-glyphs' patch-nerd-font.sh` exited 1.
  - `grep -q -- '--name' patch-nerd-font.sh` exited 1.
  - `test -f test-name-tables.sh` exited 1.
- Upstream source checked: `https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/font-patcher`
  - `--variable-width-glyphs` maps to `nonmono`.
  - `--mono` implies single-width glyph behavior.
  - A concrete `--name` string is accepted as a user-supplied name.
  - Conflicting variable-width and mono flags disable the variable-width path, so the branches must stay separate.
- Static post-change assertions:
  - Term branch includes `--mono` and not `--variable-width-glyphs`.
  - Editor branch includes `--variable-width-glyphs` and not `--mono`.
  - Pinned explicit names are `Dopemux Term Nerd Font` and `Dopemux Editor Nerd Font`.
  - The forbidden literal `name full` is absent from `patch-nerd-font.sh`.

## Validation

PASS:

- `bash -n 'docs/03-reference/Dopemux Cockpit TUI Design System/fonts/patch-nerd-font.sh' 'docs/03-reference/Dopemux Cockpit TUI Design System/fonts/test-name-tables.sh'` exited 0.
- `python -m json.tool 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-102-patch-flags-editor-proportional-family-name.json' >/dev/null` exited 0.
- `python -m jsonschema -i 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-102-patch-flags-editor-proportional-family-name.json' docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exited 0 with a jsonschema CLI deprecation warning.
- `! grep -q 'name full' 'docs/03-reference/Dopemux Cockpit TUI Design System/fonts/patch-nerd-font.sh'` exited 0.
- `grep -q 'variable-width-glyphs' 'docs/03-reference/Dopemux Cockpit TUI Design System/fonts/patch-nerd-font.sh'` exited 0.
- `git diff --check` exited 0.
- PAL `analyze`, `thinkdeep`, `planner`, `codereview`, `precommit`, and `challenge` ran; no blocking issues were identified.

NOT_RUN:

- `shellcheck`: command missing locally, exit 127.
- `test-name-tables.sh` real artifact assertions: `fontTools` is not installed, so the script exits 77.
- Full manual patch/name-table/advance-width gate: `NERD_FONTS_REPO` is unset and no local `nerd-fonts` directory or `font-patcher` file was found under `/Users/hue`; FontForge is present.

## Residual Risk / UNKNOWN

- Actual patched TTF name tables and advance widths are UNKNOWN until Nerd Fonts/font-patcher and fontTools are available.
- PR #912 must land before packet 102 can be reviewed as an isolated delta against `main`.

## Rollback

- Revert the final packet 102 commit, or delete branch `codex/cockpit-fonts-102-patch-flags`. The change is confined to the packet allowlist.
