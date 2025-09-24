# Dangerous Mode Command

> Enable Dopemux dangerous mode with no approval gates or safety restrictions

⚠️  **WARNING: This disables ALL safety mechanisms. Use only in isolated development environments!**

## Usage

```bash
/dangerous
```

## Implementation

This command executes:
```bash
dopemux start --dangerous
```

Which temporarily activates dangerous mode for the current session by setting these environment variables:

- `DOPEMUX_DANGEROUS_MODE=true`
- `HOOKS_ENABLE_ADAPTIVE_SECURITY=0`
- `CLAUDE_CODE_SKIP_PERMISSIONS=true`
- `METAMCP_ROLE_ENFORCEMENT=false`
- `METAMCP_APPROVAL_REQUIRED=false`

## What Gets Disabled

- **Approval Gates**: No more "are you sure?" prompts
- **Role Restrictions**: Access to all MCP tools immediately
- **Budget Limits**: Unlimited token usage
- **Security Hooks**: No blocking of dangerous operations
- **Audit Logging**: Reduced overhead from logging
- **Rate Limiting**: No throttling of requests

## CLI Alternatives

You can also activate dangerous mode via:
```bash
# Long flag
dopemux start --dangerous

# Short equivalent
dopemux start --dangerously-skip-permissions

# Environment override
DOPEMUX_DANGEROUS_MODE=true dopemux start
```

## Safety Notes

In dangerous mode, the AI can:
- Execute any system commands (`sudo`, `rm -rf`, etc.)
- Modify critical system files
- Make unrestricted network requests
- Access sensitive data and credentials
- Commit and push code changes automatically
- Install packages and modify system configuration

## Session Scope

⚠️  **Dangerous mode is SESSION-ONLY** - settings are not persisted to `.env` file.

## Reverting

To return to safe mode:
```bash
/safe
```

Or restart without flags:
```bash
dopemux start  # (defaults to safe mode)
```