# DMX-COCKPIT-FONTS-101 Proof Bundle

## Scope

- TP: `DMX-COCKPIT-FONTS-101-rename-plan-keys-harden-scripts`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/cockpit-fonts-101-rename-plan-keys`
- Branch: `codex/cockpit-fonts-101-rename-plan-keys`
- Base: `origin/main` at `7732c813a5e893d49646c22e097bddd00604328e`
- Repo marker: `.dopetaskroot` present
- Authority conflict: primer said base `a2396a922`, but latest user instruction required current `origin/main`; fetched `origin/main` was used.
- Claim status: task-orchestrator item was advanced from `queue` to `work`; advertised `claim_item` was not exposed in the loaded tool schema.
- PAL status: PAL MCP tools returned `Transport closed` for `listmodels`, `analyze`, `thinkdeep`, `challenge`, `planner`, `codereview`, and `precommit`.

## Files Changed

- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/private-build-plans.toml`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/build-dopemux-fonts.sh`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/patch-nerd-font.sh`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/.gitignore`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/build.md`
- `docs/03-reference/Dopemux Cockpit TUI Design System/fonts/readme.md`
- `task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-101-rename-plan-keys-harden-scripts.json`
- `proof/cockpit-fonts-101/proof-bundle.md`

## Validation

PASS:

- Baseline RED static check: `IosevkaDopemuxTerm-Regular.ttf` derives `family=IosevkaDopemuxTerm`, so the old `family == DopemuxTerm` mono guard did not fire.
- TOML parse: `python3`/`tomllib` parsed `private-build-plans.toml`; build plan keys are `DopemuxEditor`, `DopemuxTerm`; `family = "Dopemux Term"` and `family = "Dopemux Editor"` remain present.
- `bash -n '.../build-dopemux-fonts.sh' '.../patch-nerd-font.sh'` exited 0.
- Static guard substitute: `DopemuxTerm-Regular.ttf` => `mono=yes`; `DopemuxEditor-Regular.ttf` => `mono=no`; stale `IosevkaDopemuxTerm-Regular.ttf` => `fail-closed`.
- Fake Iosevka success path exited 0: non-existent `OUT_DIR` was created, original `private-build-plans.toml` was restored, manifest contained `DopemuxTerm-Regular.ttf,DopemuxEditor-Regular.ttf`, and outputs used renamed stems.
- Fake Iosevka mid-build failure path exited 42: original `private-build-plans.toml` was restored, the old TTF remained, old manifest still pointed at the old TTF, and no temp manifest remained.
- `python -m json.tool 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-101-rename-plan-keys-harden-scripts.json' >/dev/null` exited 0.
- `python -m jsonschema -i 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-101-rename-plan-keys-harden-scripts.json' docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` exited 0 with a jsonschema CLI deprecation warning.
- `! grep -rq 'IosevkaDopemux' 'docs/03-reference/Dopemux Cockpit TUI Design System/fonts/'` exited 0.
- `git diff --check` exited 0.

NOT_RUN:

- `shellcheck '.../build-dopemux-fonts.sh' '.../patch-nerd-font.sh'`: `shellcheck` command missing, exit 127.
- Full manual build+patch gate: `NERD_FONTS_REPO` is unset and no local `nerd-fonts` directory or `font-patcher` file was found under `/Users/hue` search depth. Node, npm, Python, FontForge, and a local Iosevka checkout were present, but the full toolchain was incomplete.

## Residual Risk / UNKNOWN

- Full patched-font advance-width proof is UNKNOWN because Nerd Fonts `font-patcher` was unavailable.
- Shellcheck diagnostics are UNKNOWN because `shellcheck` is not installed.
- PAL expert review is UNKNOWN because the PAL MCP transport stayed closed.

## Rollback

- Revert the final commit on this branch, or delete branch `codex/cockpit-fonts-101-rename-plan-keys`; the change is confined to the packet allowlist.
