# Dopemux Dangerous Mode Setup Guide

This guide shows you how to run Dopemux in "dangerous mode" similar to Claude Code's `--dangerously-skip-permissions` flag.

## 🎯 Current Configuration: Secure by Default

✅ **Dopemux now defaults to SAFE MODE** - all security restrictions are enabled by default.

## 🚨 Activating Dangerous Mode

### Method 1: CLI Flags (Recommended)

```bash
# Enable dangerous mode for this session only
dopemux start --dangerous

# Alternative syntax (matches Claude Code)
dopemux start --dangerously-skip-permissions
```

### Method 2: Slash Commands

Within Claude Code:
```bash
/dangerous  # Activates dangerous mode
/safe       # Returns to safe mode
```

### Method 3: Profile Management

```bash
# Switch to dangerous profile (session-persistent)
./scripts/set-profile.sh set dangerous

# Switch back to safe profile
./scripts/set-profile.sh set safe

# Check current profile
./scripts/set-profile.sh current
```

### Method 4: Environment Override

```bash
# One-time dangerous mode activation
DOPEMUX_DANGEROUS_MODE=true dopemux start
```

## 🔍 Current Status Check

```bash
# Check current security profile
./scripts/set-profile.sh current

# Expected output in safe mode:
# Current Dopemux Profile: safe
# ✅ Safe Mode Active - Full Security Enabled

# Expected output in dangerous mode:
# Current Dopemux Profile: dangerous
# ⚠️  Dangerous Mode Active - No Safety Restrictions
```

## 🚀 Quick Demo

1. **Verify safe mode (default):**
   ```bash
   ./scripts/set-profile.sh current
   ```

2. **Activate dangerous mode for one session:**
   ```bash
   dopemux start --dangerous
   ```

3. **Verify dangerous mode is active:**
   - Look for the red warning: "⚠️  DANGEROUS MODE ACTIVE"
   - No approval prompts should appear
   - All MCP tools available immediately

4. **Return to safe mode:**
   ```bash
   dopemux start  # (without flags = safe mode)
   ```

## 🔒 Security Differences

### Safe Mode (Default):
- ✅ Approval prompts for dangerous operations
- ✅ Role-based tool restrictions
- ✅ Token budget limits
- ✅ Security hook validation
- ✅ Audit logging enabled
- ✅ Rate limiting active

### Dangerous Mode:
- ❌ No approval prompts
- ❌ All tools available immediately
- ❌ Unlimited token usage
- ❌ No security validations
- ❌ Minimal logging overhead
- ❌ No rate limiting

## 🎛️ Environment Variables Set in Dangerous Mode

When dangerous mode is active, these variables are temporarily set:

```bash
DOPEMUX_DANGEROUS_MODE=true
HOOKS_ENABLE_ADAPTIVE_SECURITY=0
CLAUDE_CODE_SKIP_PERMISSIONS=true
METAMCP_ROLE_ENFORCEMENT=false
METAMCP_APPROVAL_REQUIRED=false
METAMCP_BUDGET_ENFORCEMENT=false
```

## ⚠️  Safety Guidelines

1. **Only use dangerous mode in isolated development environments**
2. **Never use in production or shared environments**
3. **Session-only activation** - settings don't persist across restarts
4. **Monitor resource usage** - unlimited budgets can be expensive
5. **Regular backups** recommended when running without restrictions

## 🔄 Integration with Claude Code

Dangerous mode automatically passes the equivalent of:
```bash
claude --dangerously-skip-permissions --no-confirm --auto-approve
```

This provides the same unrestricted experience as Claude Code's dangerous mode, but integrated with Dopemux's ADHD-optimized features and MCP orchestration.

## 📞 Troubleshooting

### If dangerous mode doesn't activate:
1. Check CLI flags: `dopemux start --help | grep dangerous`
2. Verify profile: `./scripts/set-profile.sh current`
3. Check environment: `echo $DOPEMUX_DANGEROUS_MODE`

### If you're stuck in dangerous mode:
1. Restart without flags: `dopemux start`
2. Reset profile: `./scripts/set-profile.sh set safe`
3. Check .env file doesn't have dangerous mode variables

### If you want persistent dangerous mode:
1. Edit `.env` file to set `DOPEMUX_DANGEROUS_MODE=true`
2. **NOT RECOMMENDED** - use CLI flags instead

---

**Remember: The goal is secure by default, dangerous by explicit choice!**