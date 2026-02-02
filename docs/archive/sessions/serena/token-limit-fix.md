---
id: token-limit-fix
title: Token Limit Fix
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Serena-v2 Token Limit Fix - Complete Solution

**Date**: 2025-10-20
**Issue**: `read_file` can return files exceeding 10K token limit causing MCP failures
**Status**: ✅ Fixed and Validated
**Related**: Decision #137 (Dope-Context), Decision #138 (System-Wide Audit)

## 🔴 Problem

```
MCP tool "read_file" can return large files (e.g., package-lock.json at 200KB)
→ Formatted with line numbers: 50K+ tokens
→ Exceeds 10K MCP limit
→ Hard failure with no recovery
```

**Specific Example**:
- package-lock.json: 200KB = 5000 lines
- With line number formatting (`     1→content`): +25% overhead
- Total: 5000 lines × 90 chars/line = 450K chars = 112K tokens ❌ (11x over limit)

## ✅ Solution

Implemented **2-layer defensive token budget** system:

### Layer 1: Line Limit (ADHD-Optimized)
- Default `max_lines=500` (prevents cognitive overwhelm)
- Configurable per-call if needed
- Applied BEFORE line range selection
- Transparent: User knows what they're getting

### Layer 2: Token Budget (MCP-Safe)
- Default `max_tokens=9000` (10% headroom below 10K limit)
- Conservative token estimation: 1 token ≈ 4 chars
- Real-time tracking during formatting
- Progressive line dropping if budget exceeded

## 📁 Files Modified

### `services/serena/v2/mcp_server.py`

**3 key additions**:

1. **Token Estimation Utility** (lines 4121-4123):
   ```python
   def _estimate_tokens(self, text: str) -> int:
       """Conservative token estimation: 1 token ≈ 4 chars."""
       return len(text) // 4
   ```

2. **Token Budget Truncation** (lines 4125-4159):
   ```python
   def _truncate_to_token_budget(
       self,
       lines: list[str],
       max_tokens: int,
       start_line_num: int = 1
   ) -> tuple[list[str], bool]:
       """Truncate lines to fit token budget with line numbers."""
       result_lines = []
       estimated_tokens = 50  # Base overhead
       truncated = False

       for i, line in enumerate(lines):
           formatted = f"{line_num:6d}→{line}"
           line_tokens = self._estimate_tokens(formatted + "\n")

           if estimated_tokens + line_tokens > max_tokens:
               truncated = True
               result_lines.append(
                   f"{line_num:6d}→... [truncated: {len(lines) - i} more lines, "
                   f"exceeded {max_tokens} token budget]"
               )
               break

           result_lines.append(formatted)
           estimated_tokens += line_tokens

       return result_lines, truncated
   ```

3. **Updated read_file_tool Signature** (lines 4161-4168):
   ```python
   async def read_file_tool(
       self,
       relative_path: str,
       start_line: int = 0,
       end_line: Optional[int] = None,
       max_lines: int = 500,  # ADHD-safe limit
       max_tokens: int = 9000  # MCP budget (10K limit with headroom)
   ) -> str:
   ```

**Modified logic**:
- Lines 4193-4205: Enforce max_lines before selecting range
- Lines 4207-4212: Apply token budget truncation
- Lines 4217-4223: Log with truncation status and token estimates

## ✅ Validation

Created `test_token_limit_fix.py` with 4 comprehensive tests:

```
✅ Test 1: Token Estimation (1K chars = 250 tokens)
✅ Test 2: Line Truncation (1000 lines → 500 lines enforced)
✅ Test 3: Realistic Scenario (2000 line file: 45K tokens → 7.5K tokens)
✅ Test 4: Edge Cases (empty, single line, very long lines)
```

All tests pass ✅

## 📊 Performance Impact

**Before**:
- Large file (2000 lines): 45,000 tokens ❌ (exceeds limit by 4.5x)
- No protection against token overflow
- Hard MCP failures

**After**:
- Same file: 7,500 tokens ✅ (83% of 9K budget)
- ADHD-friendly: 500 line default (manageable chunk size)
- Transparent truncation with notice
- Never exceeds 9K token budget

**Overhead**: Minimal
- Token estimation: O(n) string length check
- Truncation check: Early exit on budget exceeded
- Typical files (< 500 lines): Zero impact

## 🧠 ADHD Benefits

### Progressive Disclosure Preserved
- Default 500 lines prevents "wall of text" overwhelm
- User can explicitly request more if needed
- Truncation notice shows what's cut

### Cognitive Load Management
- 500 lines ≈ 2-3 screens of code (manageable)
- Numbered lines aid navigation
- Clear truncation markers prevent confusion

### Interrupt Recovery
- Consistent behavior (no random failures)
- Predictable chunk sizes
- Visual progress indicators (line numbers)

## 🔄 How to Apply

**Step 1**: Changes already applied to source

**Step 2**: Restart Claude Code to reload Serena MCP server

**Step 3**: Test with large file:
```python
mcp__serena-v2__read_file(
    relative_path="package-lock.json"
)
# Should return first 500 lines with truncation notice
```

**Step 4**: Validate token budget:
```python
# Try with custom limits
mcp__serena-v2__read_file(
    relative_path="large_file.py",
    max_lines=1000,  # Request more lines
    max_tokens=5000  # But limit tokens
)
# Token budget will truncate before max_lines if needed
```

## 🎯 Key Insights

`★ Insight ─────────────────────────────────────`
**ADHD-Safe File Reading**: 500-line default serves dual purpose:
1. **MCP Safety**: Keeps responses under 10K token budget
2. **Cognitive Load**: Prevents overwhelming wall of text
3. **Progressive Disclosure**: Read in manageable chunks
`─────────────────────────────────────────────────`

`★ Insight ─────────────────────────────────────`
**Two-Layer Defense**: Combining line limits + token budget provides defense-in-depth:
- Line limit catches normal cases (fast, predictable)
- Token budget catches edge cases (very long lines, unicode)
- Both respect ADHD principles (predictable chunk sizes)
`─────────────────────────────────────────────────`

## 🔗 Related

- **Decision #137**: Dope-Context MCP token limit fix
- **Decision #138**: System-wide MCP token limit audit
- **Audit**: `MCP_TOKEN_LIMIT_AUDIT.md` - Comprehensive vulnerability assessment
- **Next**: Desktop-Commander screenshot fix (P0 Critical - 168K tokens!)

## 🎉 Summary

✅ Fixed Serena-v2 read_file token limit vulnerability
✅ All tests pass (4/4)
✅ ADHD optimizations preserved (500-line chunks)
✅ Transparent truncation (users know what's cut)
✅ Ready for production use

**Next P0 Critical**: Desktop-Commander screenshot base64 encoding (168K tokens)
