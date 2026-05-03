# Dopemux CLI Command Audit Report

Date: 2026-05-01
Workspace: `/Users/hue/.codex/worktrees/e252/dopemux-mvp-wt-cockpit-pm-textual`

Companion artifacts:

- Detailed command reference: `reports/dopemux-cli-command-reference-2026-05-01.md`
- Remediation plan and implementation ledger: `reports/dopemux-cli-command-remediation-plan-2026-05-01.md`

## Summary

This audit reviewed the live `dopemux` CLI command tree as executed from the package entrypoint `dopemux.cli:main`.

Runtime inventory:

- Top-level commands: `60`
- Command/group paths excluding root: `233`
- Command/group paths including root: `234`
- Full subprocess `--help` sweep: `234` paths, `0` failures, `0` timeouts

The command tree is larger than the original planning estimate of 50 top-level commands and 137 total paths. This report uses the observed runtime tree as authority.

## Authority Used

Primary authority:

- `pyproject.toml` declares `dopemux = "dopemux.cli:main"`.
- `src/dopemux/cli.py` defines the root Click group and registers command families.
- Runtime Click traversal observed the active command tree.
- Direct executable probes used `uv run --frozen python -m dopemux ...`.

Boundary/reference authority:

- `ARCHITECTURE.md`
- `SERVICE_CATALOG.md`
- `docs/03-reference/systems/dopemux/system-dopemux.md`

Authority model applied:

- Runtime code and executable behavior outrank docs.
- `dopemux` is the operator-control layer, not canonical PM, memory, retrieval, or external execution authority.
- External handoffs remain separate authority surfaces: `scripts/taskx` -> `scripts/dopetask`, Repo Truth Extractor, task-orchestrator, ConPort, dope-memory, dope-context, Docker/MCP, launchd routing, and shell/tmux hooks.

## Findings

### P0/P1: Shell Injection Risk In MCP Service Commands

Affected commands:

- `dopemux mcp up --services`
- `dopemux mcp logs --service`
- `dopemux servers up --services`
- `dopemux servers logs --service`

Evidence:

- `src/dopemux/commands/mcp_commands.py` constructs shell strings from user-controlled service values and executes them via `subprocess.run(["bash", "-lc", cmd], ...)`.
- `servers` commands delegate directly to the `mcp` callbacks, so they inherit the same behavior.

Impact:

- Service names can be interpreted by the shell instead of treated as literal Docker Compose service arguments.
- This is a command-execution risk on an operator-facing control surface.

Recommended fix:

- Replace `bash -lc` command strings with argv lists.
- Validate service names against the active compose file or MCP registry before execution.
- Preserve exit-code propagation from Docker Compose.

### P1: Routing Mode Switching Is Broken

Affected commands:

- `dopemux routing api`
- `dopemux routing direct`

Evidence:

- `src/dopemux/routing_cli.py` defines `_set_routing_mode(config_path, mode)` as `config_path.write_text(content)`.
- `content` is undefined.
- Direct probe of `_set_routing_mode()` raised `NameError: name 'content' is not defined`.

Impact:

- Switching routing mode cannot complete when a mode change is required.
- Operator-facing success paths around LiteLLM/CCR routing are unreliable.

Recommended fix:

- Load the existing routing config, update only the mode field, preserve other keys, and write deterministic YAML.
- Add a regression test for `routing api --no-restart` and `routing direct` using a temporary routing config.

### P1: Decision Subcommands Are Missing

Affected commands:

- Expected: `dopemux decisions review`, `stats`, `show`, `list`, `graph`, `update-outcome`, `query`, and energy/pattern subcommands.
- Observed: only `decisions`, `decisions energy`, and `decisions patterns` are registered, with empty nested groups.

Evidence:

- `src/dopemux/commands/decisions_commands.py` attempts `from .commands.decisions_commands import (...)`, which resolves to a non-existent nested module path from inside `src/dopemux/commands`.
- The `ImportError` is swallowed.
- Direct probe: `dopemux decisions review --help` exits `2` with `No such command 'review'`.

Impact:

- The CLI advertises decision governance but does not expose the expected decision operations.
- The silent import failure hides command registration drift.

Recommended fix:

- Correct the import path or remove the dead registration block.
- Fail loudly in tests if expected decision commands are not registered.
- Add a command-registration snapshot test for the `decisions` family.

### P1: Code-Agent Commands Hide Runtime Failures

Affected commands:

- `dopemux code repair`
- `dopemux code analyze`
- `dopemux code code-agent-status-cmd`

Evidence:

- `src/dopemux/commands/code_commands.py` catches broad exceptions, logs the failure, and does not call `sys.exit(1)` or raise a Click exception.
- Direct probe: `dopemux code repair 'x'` logged `No module named 'genetic_agent'` and returned exit code `0`.

Impact:

- Automation and operators can receive successful exit codes for failed repair/analyze/status operations.
- This violates exit-code truthfulness for an operational command surface.

Recommended fix:

- Convert caught runtime failures to `click.ClickException` or `sys.exit(1)`.
- Add tests asserting non-zero exit on missing agent dependencies and failed agent calls.

### P1: MCP Status And Logs Can Mask Docker Failures

Affected commands:

- `dopemux mcp status`
- `dopemux mcp logs`
- `dopemux servers status`
- `dopemux servers logs`

Evidence:

- `src/dopemux/commands/mcp_commands.py` calls Docker with `check=False`.
- The surrounding `except CalledProcessError` cannot fire for non-zero Docker exits when `check=False`.

Impact:

- Docker failures can return CLI success.
- Health/status automation cannot rely on these exit codes.

Recommended fix:

- Capture the subprocess result and exit with its return code.
- Keep logs streaming behavior, but preserve final command failure when Docker exits non-zero.

### P2: Help Exposes Internal Command Names

Affected commands:

- `dopemux update update-status-cmd`
- `dopemux code code-agent-status-cmd`

Evidence:

- Direct probes show `dopemux update status --help` and `dopemux code status --help` return `No such command`.
- The live commands retain function-derived names instead of operator-facing names.

Impact:

- Operator ergonomics and discoverability are poor.
- Docs or scripts may reasonably expect `status` subcommands under these groups.

Recommended fix:

- Register aliases: `update status` and `code status`.
- Keep old names only as compatibility aliases if needed.

### P2: Profile Placeholders Are Exposed As Real Commands

Affected commands:

- `dopemux profile copy`
- `dopemux profile edit`
- `dopemux profile delete`
- `dopemux profile current`

Evidence:

- `src/dopemux/commands/profile_commands.py` registers these commands, but each raises `click.ClickException("... is not implemented yet")`.

Impact:

- Help output advertises commands that cannot perform work.
- Operators cannot tell from command listing that these are placeholders.

Recommended fix:

- Either implement them, hide them, or mark them explicitly as unavailable in help text.

### P2: Native Hook Registration Is Duplicated And Can Discard Bad JSON

Affected command:

- `dopemux native-hooks register`

Evidence:

- `native-hooks` is defined twice in `src/dopemux/cli.py`.
- The later registration wins.
- JSON parsing of existing settings catches all exceptions and continues with `{}`, which can overwrite unreadable or invalid settings content.

Impact:

- Command authority is drifted in one large file.
- Invalid settings can be silently replaced instead of fail-closed.

Recommended fix:

- Keep one command definition.
- Fail with an explicit error when existing settings JSON cannot be parsed.
- Write via a temporary file and preserve a backup before modifying Claude settings.

### P2: `pr-merge` Registration Authority Is Drifted

Affected command:

- `dopemux pr-merge`

Evidence:

- `src/dopemux/cli.py` registers an earlier Click wrapper and later overwrites it with an argparse delegate using `add_help_option=False`.
- Direct probe confirms help works through the later argparse delegate.

Impact:

- Runtime behavior is currently acceptable for help, but source ownership is confusing and easy to regress.

Recommended fix:

- Keep a single registration path for `pr-merge`.
- Add a smoke test for `dopemux pr-merge --help`.

## Command-Family Appendix

| Family | Paths Observed | Authority / Notes |
| --- | ---: | --- |
| root | 1 | Root Click group from `dopemux.cli:main`. |
| agent | 4 | Claude tools agent messaging; tmux/session dependent. |
| agent-loop | 3 | Local agent-loop orchestration helpers. |
| analyze | 1 | Writes analysis artifacts under `.dopemux/analysis` unless output overridden. |
| audit | 4 | Documentation audit and wizard surfaces. |
| autoresponder | 6 | Claude auto-responder setup/start/stop/config. |
| backup/save | 2 | Same context-save callback exposed under two names. |
| capture | 3 | Chronicle capture ingestion. |
| cockpit | 2 | Static/textual PM operator surface. |
| code | 4 | Code-agent surface; failure exit-code issue found. |
| debug | 10 | Claude tools debug session surface. |
| decisions | 3 | Registration drift; expected subcommands missing. |
| dev | 4 | Contributor/development mode commands. |
| env | 5 | Environment inspection helpers. |
| extract | 5 | Document extraction and canonical `truth-run` path. |
| extractor | 12 | Legacy promptset/prescan support plus aliases. |
| health/doctor/status | 3 | Health/status diagnostics; some live checks are environment dependent. |
| hooks/native-hooks | 3 | Hook setup and native Claude settings mutation. |
| instances | 4 | Instance listing/resume/cleanup. |
| kernel | 9 | Delegates to `scripts/taskx`, which execs `scripts/dopetask`. |
| mcp/servers | 11 | Docker/MCP control; injection and exit-code issues found. |
| memory | 9 | Rollup and capture ingestion. |
| mobile/mobile-env | 10 | Mobile/tmux environment helpers. |
| personas | 3 | Persona list/show surface. |
| pr-merge | 1 | Argparse delegate; focused tests show two failures in specialist suite. |
| profile/switch | 18 | Profile management and compatibility alias. |
| routing | 16 | launchd/LiteLLM/CCR routing; mode switching bug found. |
| rte/upgrades/truth | 22 | Repo Truth Extractor canonical and legacy surfaces. |
| run-build/run-tests | 2 | Pass-through subprocess commands with mobile notifications. |
| safe/session/shell-setup/theme/layouts/launch/dope/quick/task/wire-conport/extractpro/extract-chatlog/repscan/dashboard | 18 | Mixed helper, compatibility, and operational commands. |
| tmux | 13 | Tmux session/pane control. |
| trigger | 3 | Hook telemetry emitters. |
| update | 5 | Update/rollback/status surface; status command name drift found. |
| workflow | 11 | Local workflow plus workflow API calls. |

## Drift Appendix

- Plan drift: original plan expected 50 top-level commands and 137 total paths; runtime has 60 top-level commands and 233 paths.
- Docs drift at audit time: `system-dopemux.md` mentioned an old CLI import failure, but current root help succeeds under `uv run --frozen`. The companion remediation pass updates this doc note.
- Naming drift: `kernel` help still says TaskX, while observed execution path is `scripts/taskx` -> `scripts/dopetask` -> external `dopetask`.
- Alias drift: `upgrades` and `extractor` remain legacy paths around the canonical `rte` surface.
- Registration drift at audit time: `native-hooks`, `pr-merge`, and `instances` were registered more than once in `cli.py`. The companion remediation pass consolidates these surfaces.

## Validation Performed

Commands/checks run:

- `uv run --frozen python -m dopemux --help`
  - Exit: `0`
- Runtime Click traversal
  - Top-level commands: `60`
  - Paths excluding root: `233`
  - Paths including root: `234`
- In-process help sweep
  - Paths: `234`
  - Failures: `0`
- Full subprocess help sweep
  - Paths: `234`
  - Workers: `8`
  - Per-command timeout: `30s`
  - Elapsed: `50.79s`
  - Failures: `0`
  - Timeouts: `0`
- Focused CLI tests
  - Result: `148 passed`, `2 failed`
  - Failing tests:
    - `tests/pr_merge_specialist/test_policy_and_validation.py::test_module_entrypoint_works_without_pythonpath`
    - `tests/pr_merge_specialist/test_queue_drain_integration.py::test_train_filters_ineligible_strategies`
- Direct probes:
  - `dopemux decisions review --help` exited `2`.
  - `dopemux code repair 'x'` exited `0` despite missing `genetic_agent`.
  - `_set_routing_mode()` raised `NameError`.
  - `dopemux routing health` exited `1` in the local environment because LiteLLM readiness was unavailable.
- `git diff --check`
  - Exit: `0`

## Commands Intentionally Not Executed

The following side-effectful commands were audited through help/source/tests rather than live execution:

- `dopemux start`
- `dopemux init`
- `dopemux mcp up/down`
- `dopemux servers up/down`
- `dopemux routing install/uninstall/start/stop/reload/api/direct/repair/sync-keys`
- `dopemux update run/rollback/resume`
- `dopemux hooks --setup/--teardown/--install-shell-hooks`
- `dopemux native-hooks register`
- `dopemux tmux send/stop/start/open/close`

## Residual Risk

The full subprocess help sweep proves importability and help rendering for the observed command tree. It does not prove live side-effectful behavior is safe. The highest-priority next work is to fix shell execution in MCP commands, repair routing mode writes, restore decision command registration, and enforce non-zero exits for failed code-agent operations.
