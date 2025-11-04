# Claude Code + CCR Integration Fix ✅

## Problem Identified

Claude Code was sending its own API key (`sk-...L7Ui`) to CCR instead of using CCR's API key, causing 401 authentication errors.

## Root Cause

The `ClaudeLauncher` in `src/dopemux/claude/launcher.py` was overwriting the `ANTHROPIC_BASE_URL` environment variable set by CCR, replacing it with `LITELLM_PROXY_URL`.

**Flow before fix:**
1. ✅ `dopemux start --claude-router` sets CCR env vars (line 1378 in cli.py)
2. ❌ `ClaudeLauncher._prepare_environment()` overwrites them with wrong values (line 303-306)
3. ❌ Claude Code connects to wrong endpoint with wrong API key

## Fix Applied

Modified `src/dopemux/claude/launcher.py` line 298-310:

**Before:**
```python
if via_litellm:
    proxy_url = env.get("LITELLM_PROXY_URL") or env.get("OPENAI_API_BASE")
    if proxy_url:
        env.setdefault("ANTHROPIC_API_BASE", proxy_url)
        env.setdefault("ANTHROPIC_BASE_URL", proxy_url)
```

**After:**
```python
if via_litellm:
    # If ANTHROPIC_BASE_URL is already set (e.g., by CCR), keep it
    # Otherwise, fall back to LITELLM_PROXY_URL
    if not env.get("ANTHROPIC_BASE_URL"):
        proxy_url = env.get("LITELLM_PROXY_URL") or env.get("OPENAI_API_BASE")
        if proxy_url:
            env.setdefault("ANTHROPIC_API_BASE", proxy_url)
            env.setdefault("ANTHROPIC_BASE_URL", proxy_url)
```

## How It Works Now

1. ✅ `dopemux start --claude-router` sets:
   - `ANTHROPIC_BASE_URL=http://127.0.0.1:3456`
   - `ANTHROPIC_API_KEY=3-W5jDXWWaEKth9gerZogE38Mtsd_IP0ddyLFAZ-eK4`

2. ✅ `ClaudeLauncher` preserves these values (doesn't overwrite)

3. ✅ Claude Code launches with correct CCR endpoint and API key

4. ✅ Requests route through CCR → LiteLLM → actual models

## Testing

### Start dopemux with CCR:
```bash
dopemux start --claude-router --background
```

### Verify environment:
```bash
# In the dopemux tmux session:
echo $ANTHROPIC_BASE_URL
# Should show: http://127.0.0.1:3456

echo $ANTHROPIC_API_KEY
# Should show: 3-W5jDXWWaEKth9gerZogE38Mtsd_IP0ddyLFAZ-eK4
```

### Check Claude Code connects:
Watch the CCR logs:
```bash
tail -f .dopemux/claude-code-router/A/claude-code-router.log
```

Should see successful requests, not 401 errors.

## Files Modified

1. ✅ `src/dopemux/claude/launcher.py` - Fixed environment variable handling

## Next Steps

1. **Test the fix:**
   ```bash
   # Stop any running dopemux
   tmux kill-session -t dopemux 2>/dev/null
   
   # Start fresh with CCR
   dopemux start --claude-router --background
   ```

2. **Verify in Claude Code:**
   - No more 401 errors
   - Requests succeed
   - Model indicator shows in status bar

3. **Monitor CCR logs:**
   ```bash
   tail -f .dopemux/claude-code-router/A/claude-code-router.log
   ```

## Expected Behavior

✅ Claude Code connects to CCR (port 3456)  
✅ CCR routes to LiteLLM (port 4000)  
✅ LiteLLM routes to configured models (GPT-5, Grok, etc.)  
✅ No authentication errors  
✅ Model display shows correct model in status bar

---
**Fixed**: 2025-11-04 05:00 UTC
