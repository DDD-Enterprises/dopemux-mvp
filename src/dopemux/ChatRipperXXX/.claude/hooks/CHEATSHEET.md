# Smart Hooks Cheat Sheet

## Enable Features
```bash
export HOOKS_ENABLE_SMART_OPTIMIZATION=1    # Token tracking
export HOOKS_ENABLE_ADAPTIVE_SECURITY=1     # Security learning
```

## Dashboards
```bash
python .claude/hooks/dashboard.py           # Token usage
python .claude/hooks/security_dashboard.py  # Security decisions
```

## Token Savers
| Tool | Problem | Solution |
|------|---------|----------|
| TaskMaster | ~21k tokens | `status=pending withSubtasks=false` |
| ConPort | ~17k tokens | `limit=3-5` on searches |
| Zen | ~29k tokens | `files≤1` + reuse `continuation_id` |
| Serena | ~15k tokens | Use `find_symbol` not `read_file` |

## Security Examples
```bash
# ✅ Auto-allowed
git status, python -m pytest, npm test

# ⚠️ Asks first  
npm install package, pip install package

# 🚫 Blocked
sudo commands, rm -rf operations
```

## Quick Test
```bash
# Test everything works
export HOOKS_ENABLE_SMART_OPTIMIZATION=1 HOOKS_ENABLE_ADAPTIVE_SECURITY=1
python .claude/hooks/dashboard.py --patterns
python .claude/hooks/security_dashboard.py --summary
```

## Turn Off
```bash
export HOOKS_ENABLE_SMART_OPTIMIZATION=0
export HOOKS_ENABLE_ADAPTIVE_SECURITY=0
```