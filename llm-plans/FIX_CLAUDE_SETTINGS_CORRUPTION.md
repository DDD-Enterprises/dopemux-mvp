# Fix Claude Code Settings Corruption

## Objective
Resolve the `Settings Error` in `.claude/settings.json` caused by Dopemux CLI injecting legacy hook keys and ensure future registrations follow the correct Claude Code schema.

## Key Files & Context
- `src/dopemux/cli.py`: Contains duplicated `native-hooks register` command logic and lacks cleanup of legacy keys.
- `src/dopemux/claude_config.py`: Sanitizes Claude configuration but needs to be more aggressive in fixing hook schema errors.

## Implementation Steps

### 1. Fix `src/dopemux/cli.py`
- Remove the duplicated `@cli.group("native-hooks")` and associated `register` command (around lines 3958-4030).
- Remove duplicated `cli.add_command` calls for `instances`, `personas`, and `native_hooks`.
- Update `native_hooks_register` to explicitly delete legacy hook keys from the `hooks` section before merging new configuration.
- Legacy keys to remove: `Start`, `Stop`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`.

### 2. Update `src/dopemux/claude_config.py`
- Enhance `_sanitize_config` to identify top-level event keys in the `hooks` section.
- Automatically migrate these legacy keys into the `command` array format if they are found.
- Ensure `UserPromptSubmit` and other hooks always have a `matcher` if they are in the old format (though migration to `command` is preferred).

### 3. Manual Verification
- Run `dopemux native-hooks register` and verify `.claude/settings.json` is correctly formatted.
- Run `claude --version` or a simple `claude` command to ensure no settings errors are reported.

## Verification & Testing
- Check that `settings.json` no longer contains top-level keys like `Start` or `Stop`.
- Verify that `dopemux native-hooks register` only adds/updates the `command` block.
- Confirm that the `native-hooks` command group is not duplicated in `dopemux --help`.
