# DMX-COCKPIT-FONTS-103 Proof Bundle

## Packet

- TP ID: `DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile`
- TP path: `task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile.json`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/cockpit-fonts-103-css-matrix`
- Branch: `codex/cockpit-fonts-103-css-matrix`
- Base: `origin/codex/cockpit-fonts-102-patch-flags` at `957fbc4437f8df25f7c1562cd3a2c1178be57f8a`

## Files Changed

- `docs/03-reference/Dopemux Cockpit TUI Design System/colors_and_type.css`
- `task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile.json`
- `proof/cockpit-fonts-103/proof-bundle.md`

## Changes

- Replaced the incomplete two-entry raw Term `@font-face` set with a 12-entry Nerd Font matrix:
  - `Dopemux Term Nerd Font` x Regular/Medium x normal/italic/oblique.
  - `Dopemux Editor Nerd Font` x Regular/Medium x normal/italic/oblique.
- Updated `--font-mono` to prefer `"Dopemux Term Nerd Font"`.
- Updated `--font-editor` to prefer `"Dopemux Editor Nerd Font"`.
- Preserved Medium as one family with `font-weight: 500 700`.
- Preserved italic and oblique as distinct `font-style` values.
- Removed the stale `DopemuxTerm Nerd Font` token from the CSS.

## Static Evidence

- Static matrix validator result: `PASS`
- `@font-face` count: `12`
- Missing expected faces: `[]`
- Extra faces: `[]`
- Expected patched output paths are all under `fonts/out/nerd-font/`.

## Validations

| Validation | Exit | Result |
| --- | ---: | --- |
| `python -m json.tool 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile.json' >/dev/null` | 0 | PASS |
| `python -m jsonschema -i 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile.json' docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | 0 | PASS |
| `! grep -q 'DopemuxTerm Nerd Font' 'docs/03-reference/Dopemux Cockpit TUI Design System/colors_and_type.css'` | 0 | PASS |
| `git diff --check` | 0 | PASS |
| Static CSS matrix validator | 0 | PASS |
| `pre-commit run --files 'docs/03-reference/Dopemux Cockpit TUI Design System/colors_and_type.css' 'task-packets/generated/DMX-COCKPIT-FONTS/DMX-COCKPIT-FONTS-103-css-font-face-matrix-reconcile.json' 'proof/cockpit-fonts-103/proof-bundle.md'` | 0 | PASS |

## PAL / Orchestrator

- PAL required chain for this packet: `analyze -> planner -> codereview -> precommit`.
- PAL status: `NOT_RUN`; `mcp__pal.analyze`, `mcp__pal.planner`, `mcp__pal.codereview`, and `mcp__pal.precommit` returned `Transport closed` on attempts.
- Task-orchestrator status: `NOT_RUN`; earlier 103 `get_context` / `get_next_status` attempts returned `Transport closed`.
- Task-orchestrator retry status: `NOT_RUN`; `mcp__task_orchestrator.get_context` returned `Transport closed`.

## Review / Precommit Status

- Codereview status: manual review PASS; PAL codereview NOT_RUN due `Transport closed`.
- Precommit status: local pre-commit PASS; PAL precommit NOT_RUN due `Transport closed`.

## Commit / PR

- Commit SHA: final SHA recorded in final/orchestrator proof after commit creation.
- PR URL: created after commit/push; final URL recorded in final/orchestrator proof.

## Residual Risks / UNKNOWNs

- The packet is stacked on unmerged 101/102 branches because those PRs are still open. Merge ordering must preserve `#912 -> #914 -> this packet`.
- Runtime browser loading of local font files was not exercised in this packet; evidence is static CSS/file-name reconciliation only.
- MCP PAL/task-orchestrator availability is currently `UNKNOWN` due transport closure.
