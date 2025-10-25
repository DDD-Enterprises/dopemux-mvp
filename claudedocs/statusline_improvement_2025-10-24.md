# Statusline Investigation - Claude Code JSON Fields

**Date**: 2025-10-24
**Conclusion**: Original statusline approach was correct all along!

## Investigation Results

### What We Thought
Claude Code might provide direct context window data in JSON:
- `.context.used` - Tokens used
- `.context.total` - Total context window

### What We Found
According to Claude Code documentation, the statusline JSON **does NOT** include these fields.

**Available Fields** (per [docs.claude.com/claude-code/statusline](https://docs.claude.com/en/docs/claude-code/statusline)):
```json
{
  "transcript_path": "/path/to/transcript.jsonl",
  "model": {
    "id": "claude-opus-4-1",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/path/to/dir"
  },
  "cost": {
    "total_cost_usd": 0.50,
    "total_duration_ms": 120000,
    "total_lines_added": 42,
    "total_lines_removed": 15
  },
  "exceeds_200k_tokens": true  // Added in v1.0.88
}
```

## What We Added

**Claude Code v1.0.88** introduced: `exceeds_200k_tokens` (boolean)

This is a **warning flag**, not the actual usage count.

### Enhancement Made

Added `exceeds_200k_tokens` warning to `.claude/statusline.sh`:

```bash
# Check for 200K+ token warning (Claude Code v1.0.88+)
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false' 2>/dev/null)

# ... later in output ...

# Warning if exceeds 200K (Claude Code v1.0.88+)
if [ "$exceeds_200k" = "true" ]; then
    printf " \033[31m⚠️>200K\033[0m"
fi
```

**Statusline Output**: When context exceeds 200K:
```
dopemux-mvp main | ✅ Component 6 [2h 15m] | 🧠 ⚡= 👁️● 215K/1000K (21%) ⚠️>200K | Sonnet
```

## Why Original Approach Was Correct

The original statusline:
1. ✅ Parses `transcript_path` for accurate token counts (STILL NEEDED)
2. ✅ Detects model ID to infer context window size (STILL NEEDED)
3. ✅ Uses safe defaults for unknown models (STILL NEEDED)
4. ✅ Now includes `exceeds_200k_tokens` warning (NEW)

Claude Code does not provide:
- ❌ Direct `.context.used` count
- ❌ Direct `.context.total` window size
- ❌ Any alternative token tracking fields

## Conclusion

**Keep the original statusline** with the new `exceeds_200k_tokens` enhancement.

The "improved" version that tried to use `.context.*` fields was based on incorrect assumptions and has been removed.

## Files Modified

- `.claude/statusline.sh` - Added `exceeds_200k_tokens` warning (lines 93, 279-281)

## Files Removed

- `.claude/statusline-improved.sh` - Based on incorrect assumptions about available JSON fields
- `scripts/capture_statusline_input.sh` - No longer needed
- `scripts/test_statusline_improvement.sh` - No longer needed
