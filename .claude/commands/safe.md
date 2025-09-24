# Safe Mode Command

> Enable Dopemux safe mode with full security restrictions and approval gates

✅ **PRODUCTION SAFE: Enables all security mechanisms and approval workflows**

## Usage

```bash
/safe
```

This command will:
1. Disable dangerous mode settings
2. Enable all approval requirements
3. Restore role-based tool access restrictions
4. Apply token budget limits
5. Enable all security validations and audit logging

## What Gets Enabled

- **Approval Gates**: Confirmation prompts for dangerous operations
- **Role Restrictions**: Tools available based on current role only
- **Budget Limits**: Token usage tracking and limits
- **Security Hooks**: Blocking of potentially dangerous operations
- **Audit Logging**: Full logging of all operations
- **Rate Limiting**: Request throttling per role

## Equivalent To

This is equivalent to running Claude Code with normal security:
```bash
claude  # (default safe mode)
```

## Security Features

In safe mode, the system will:
- Require approval for system-level operations
- Block dangerous commands like `sudo`, `rm -rf`
- Limit tool access based on your current role
- Track and limit token usage
- Log all operations for audit
- Require escalation for powerful tools

## Role-Based Access

Tools are mounted based on your role:
- **Developer**: Code editing, testing, basic analysis
- **Researcher**: Information gathering, documentation access
- **Architect**: System design tools, analysis frameworks
- **Debugger**: Problem-solving tools, deep analysis

## Switching Back

To return to dangerous mode (development only):
```bash
/dangerous
```

Or use the profile management script:
```bash
./scripts/set-profile.sh set dangerous
```