# Dopemux CLI Audit Implementation Notes

Date: 2026-05-01
Workspace: `/Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual`

## Changes Implemented

- Added the detailed command reference report at `reports/dopemux-cli-command-reference-2026-05-01.md`.
- Added the remediation ledger at `reports/dopemux-cli-command-remediation-plan-2026-05-01.md`.
- Linked both companion artifacts from `reports/dopemux-cli-command-audit-2026-05-01.md`.
- Hardened MCP/server commands by validating compose services, avoiding shell-interpolated subprocess calls, and propagating Docker failures.
- Fixed routing mode writes to update YAML deterministically while preserving existing config fields.
- Removed the broken decisions self-import and kept only the runtime-backed decisions groups.
- Made code-agent commands fail nonzero on missing dependencies or failed operations; added public `code status` with the old generated name hidden.
- Added public `update status` with the old generated name hidden.
- Replaced profile placeholder commands with the real profile lifecycle callbacks.
- Consolidated duplicate `instances`, `native-hooks`, and `pr-merge` registration paths.
- Made native hook registration fail closed on invalid `settings.json` and write atomically with a backup.
- Fixed PR merge specialist self-check behavior under `--allow-dirty` and train filtering for mixed staged strategies.
- Synchronized PR merge specialist template modules required by the repository parity contract.
- Updated the stale Dopemux system doc note about root CLI import failure.

## Validation

- `uv run --frozen python -m dopemux --help`: exit `0`.
- Full subprocess help sweep from runtime Click traversal: `236` paths, `0` failures.
- Focused remediation tests: exit `0`.
- Full focused suite from the approved plan: exit `0`.
- `git diff --check`: exit `0`.

## Remaining Risk

- `AGENTS.md` was already modified before this implementation and was not touched.
- Live side-effectful integrations were not executed: Docker Compose service startup, launchd install/reload, tmux mutation, hook installation against real user settings, update rollback, or GitHub PR mutation.
- Decision-management leaf commands remain absent because no canonical runtime callbacks were found in `src/dopemux`.
