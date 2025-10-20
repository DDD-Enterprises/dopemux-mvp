# MCP Token Limit - Comprehensive Security Audit

**Date**: 2025-10-20
**Auditor**: System-wide token budget analysis
**Scope**: All Dopemux MCP servers
**Critical Issue**: 10K token hard limit in Claude Code MCP transport

## 🎯 Executive Summary

**Status**: 🔴 **CRITICAL** - Multiple MCP servers vulnerable to token limit failures

**Fixed**:
- ✅ Dope-Context (Decision #137)
- ✅ Serena-v2 (Decision #139)
- ✅ ConPort (Decision #141)
- ✅ Zen (Decision #142)
- ✅ GPT-Researcher (Decision #143)
- ✅ Leantime-Bridge (Decision #144)

**Validated Safe**:
- ✅ Desktop-Commander (Decision #140 - already uses file path pattern)
- 🟢 Context7 (LOW RISK - external service)

---

## 📊 Risk Matrix

| MCP Server | Risk Level | Failure Mode | Max Observed | Status |
|------------|-----------|--------------|--------------|--------|
| **Serena-v2** | 🟢 FIXED | `read_file` on large files | Was Unknown | ✅ Decision #139 |
| **Desktop-Commander** | 🟢 SAFE | File path (no base64) | ~30 tokens | ✅ Decision #140 |
| **ConPort** | 🟢 FIXED | `get_decisions` with 100+ items | Was 15K | ✅ Decision #141 |
| **Zen** | 🟢 FIXED | Multi-step `thinkdeep` analysis | Was 20K | ✅ Decision #142 |
| **GPT-Researcher** | 🟢 FIXED | Research reports with sources | Was 14.5K | ✅ Decision #143 |
| **Leantime-Bridge** | 🟢 FIXED | Large project/ticket lists | Was 15K | ✅ Decision #144 |
| **Dope-Context** | 🟢 FIXED | Large search result sets | Was 12K | ✅ Decision #137 |
| **Context7** | 🟢 LOW | External MCP (not our code) | N/A | N/A |

---

## 🔴 P0: Critical Vulnerabilities

### 1. Serena-v2 MCP - File Reading

**Vulnerable Tool**: `read_file`

**Risk**: Reading large files (>40KB) will exceed 10K token limit

**Failure Scenario**:
```python
# This will fail on large files
mcp__serena-v2__read_file(relative_path="package-lock.json")
# package-lock.json = 200KB = 50K tokens → HARD FAILURE
```

**Impact**:
- Cannot read common large files (package-lock.json, yarn.lock, large configs)
- Breaks code navigation workflows
- Silent failures frustrate users

**Solution Required**:
```python
# Add truncation with line limits
async def read_file(
    relative_path: str,
    start_line: int = 0,
    end_line: Optional[int] = None,
    max_lines: int = 500,  # NEW: ADHD-safe limit
    max_tokens: int = 9000  # NEW: Budget enforcement
) -> Dict:
    # Read file
    content = read_full_file(path)

    # Apply line limits
    lines = content.split('\n')
    if end_line is None or end_line > start_line + max_lines:
        end_line = start_line + max_lines

    truncated_content = '\n'.join(lines[start_line:end_line])

    # Token budget check
    if estimate_tokens(truncated_content) > max_tokens:
        # Further truncate
        truncated_content = progressive_line_truncation(truncated_content, max_tokens)

    return {
        "content": truncated_content,
        "truncated": end_line < len(lines),
        "total_lines": len(lines),
        "lines_returned": end_line - start_line
    }
```

**Estimated Fix Time**: 2 hours

---

### 2. Desktop-Commander MCP - Screenshot Encoding

**Vulnerable Tool**: `screenshot`

**Risk**: Base64-encoded screenshots are 4/3× larger than binary

**Failure Scenario**:
```python
# 1920×1080 PNG screenshot ≈ 2MB binary
# Base64 encoded ≈ 2.7MB = 675K chars = 168K tokens
# → MASSIVELY EXCEEDS 10K LIMIT
mcp__desktop-commander__screenshot(filename="/tmp/screen.png")
```

**Impact**:
- **SEVERE**: Screenshots completely broken
- Core ADHD feature (visual memory aids) non-functional
- No workaround available to users

**Solution Required**:
```python
# Option 1: Return file path only (recommended)
async def screenshot(filename: str) -> Dict:
    take_screenshot(filename)

    return {
        "status": "success",
        "file_path": filename,  # Return path, not content
        "size_bytes": os.path.getsize(filename),
        "note": "Screenshot saved to disk. Use file path to access."
    }

# Option 2: Thumbnail + path
async def screenshot(filename: str, include_thumbnail: bool = False) -> Dict:
    take_screenshot(filename)

    result = {
        "status": "success",
        "file_path": filename
    }

    if include_thumbnail:
        # 200×150 thumbnail = ~30KB base64 = 7.5K tokens (safe)
        thumbnail_base64 = create_thumbnail(filename, max_size=(200, 150))
        result["thumbnail"] = thumbnail_base64
        result["thumbnail_note"] = "Thumbnail for preview only. Use file_path for full image."

    return result
```

**Estimated Fix Time**: 3 hours

---

## 🟡 P1: Medium Risk Vulnerabilities

### 3. ConPort MCP - Bulk Queries

**Vulnerable Tools**:
- `get_decisions` (with limit=100)
- `get_progress` (with limit=100)
- `get_custom_data` (entire categories)
- `search_decisions_fts` (many results)

**Risk**: Returning 50-100 decisions with full details exceeds budget

**Failure Scenario**:
```python
# 100 decisions × 150 tokens each = 15K tokens
mcp__conport__get_decisions(workspace_id="...", limit=100)
```

**Impact**:
- Large projects with many decisions fail to load
- Historical queries break
- ADHD context restoration fails

**Solution Required**:
```python
# Add progressive truncation
async def get_decisions(
    workspace_id: str,
    limit: Optional[int] = None,
    max_tokens: int = 9000  # NEW
) -> List[Dict]:
    # Get decisions from DB
    decisions = query_decisions(workspace_id, limit)

    # Build results with budget tracking
    results = []
    tokens_used = 200  # Base overhead

    for decision in decisions:
        # Truncate implementation_details if needed
        truncated_decision = {
            "id": decision.id,
            "summary": decision.summary,
            "rationale": decision.rationale[:500],  # Limit rationale
            "implementation_details": decision.implementation_details[:800],  # Limit details
            "tags": decision.tags,
            "timestamp": decision.timestamp
        }

        item_tokens = estimate_tokens(json.dumps(truncated_decision))

        if tokens_used + item_tokens > max_tokens:
            break  # Stop adding

        results.append(truncated_decision)
        tokens_used += item_tokens

    return results
```

**Estimated Fix Time**: 4 hours (multiple tools)

---

### 4. Zen MCP - Multi-Step Analysis

**Vulnerable Tools**:
- `thinkdeep` (multi-step investigation)
- `planner` (incremental planning)
- `consensus` (multi-model responses)
- `codereview` (comprehensive analysis)

**Risk**: Accumulating multiple steps + full code snippets in response

**Failure Scenario**:
```python
# Step 10 of debugging includes full stack trace + code + previous findings
mcp__zen__debug(
    step="Final analysis with full context",
    step_number=10,
    findings="..."  # Includes all 9 previous steps
)
# Total response: 20K tokens
```

**Impact**:
- Long analysis sessions fail mid-workflow
- Ultrathink features break
- Research-backed decisions incomplete

**Solution Required**:
```python
# Zen already uses continuation_id for sessions
# Add response truncation:
async def thinkdeep(...) -> Dict:
    # Process thinking step
    analysis_result = await run_analysis(...)

    # Apply budget to assistant response
    if estimate_tokens(json.dumps(analysis_result)) > 9000:
        # Truncate verbose fields
        analysis_result["findings"] = truncate_text(
            analysis_result["findings"],
            max_chars=2000
        )
        analysis_result["step"] = truncate_text(
            analysis_result["step"],
            max_chars=3000
        )
        analysis_result["_truncated"] = True

    return analysis_result
```

**Estimated Fix Time**: 5 hours (multiple tools, complex)

---

## 🟡 P2: Lower Risk

### 5. GPT-Researcher MCP

**Vulnerable Tool**: `deep_research`

**Risk**: Research reports with 20+ sources + full synthesis

**Solution**: Already returns `research_id` for long content. Consider adding:
```python
# Truncate source excerpts in initial response
# Full content available via research_id lookup
```

**Estimated Fix Time**: 2 hours

---

## ✅ Fixed

### 6. Dope-Context MCP
**Status**: ✅ FIXED (Decision #137)
**Solution**: 3-layer progressive truncation
**Budget**: 9K tokens with 10% headroom

---

## 🛠️ Recommended Fix Pattern

**Create reusable MCP response wrapper**:

```python
# services/shared/mcp_response_budget.py

from typing import Any, Dict, List
import json

MCP_MAX_TOKENS = 10000
SAFE_BUDGET = 9000

def estimate_tokens(text: str) -> int:
    """Conservative token estimation: 1 token ≈ 4 chars."""
    return len(text) // 4

def enforce_mcp_budget(
    response: Any,
    budget: int = SAFE_BUDGET,
    truncate_fields: List[str] = None
) -> tuple[Any, bool]:
    """
    Enforce token budget on MCP response.

    Args:
        response: MCP response object (dict, list, or primitive)
        budget: Token budget (default 9K)
        truncate_fields: Fields to truncate if over budget

    Returns:
        (truncated_response, was_truncated)
    """
    # Estimate current size
    json_str = json.dumps(response)
    current_tokens = estimate_tokens(json_str)

    if current_tokens <= budget:
        return response, False

    # Apply truncation strategy
    if isinstance(response, list):
        # List truncation: drop items from end
        truncated = []
        tokens_used = 50  # Base overhead

        for item in response:
            item_tokens = estimate_tokens(json.dumps(item))
            if tokens_used + item_tokens > budget:
                break
            truncated.append(item)
            tokens_used += item_tokens

        return truncated, True

    elif isinstance(response, dict) and truncate_fields:
        # Dict field truncation
        truncated = response.copy()
        for field in truncate_fields:
            if field in truncated and isinstance(truncated[field], str):
                truncated[field] = truncated[field][:2000] + "... [truncated]"

        return truncated, True

    return response, False
```

---

## 📝 Action Plan

### Phase 1: Critical Fixes (Week 1)
1. ✅ Dope-Context (DONE)
2. 🔴 Serena-v2 `read_file` truncation
3. 🔴 Desktop-Commander screenshot path-only return

### Phase 2: Medium Risk (Week 2)
4. 🟡 ConPort bulk query truncation
5. 🟡 Zen multi-step response budgeting

### Phase 3: Hardening (Week 3)
6. 🟡 GPT-Researcher report truncation
7. 📚 Create shared `mcp_response_budget` utility
8. 📖 Document MCP token budgeting best practices

---

## 🎓 Lessons Learned

`★ Key Insight ─────────────────────────────────────`
**MCP Token Budgeting is Non-Negotiable**: Every MCP tool returning variable-sized content MUST implement defensive truncation. The 10K limit is enforced at the transport layer and will cause hard failures with no recovery.
`─────────────────────────────────────────────────────`

`★ Key Insight ─────────────────────────────────────`
**Base64 Encoding Kills Budgets**: A 2MB screenshot becomes 168K tokens when base64-encoded. Return file paths instead of encoding large binary data.
`─────────────────────────────────────────────────────`

`★ Key Insight ─────────────────────────────────────`
**Progressive Truncation Preserves UX**: Truncating lowest-scored results first maintains ADHD-optimized progressive disclosure while staying within budget.
`─────────────────────────────────────────────────────`

---

## 📚 References

- **Decision #137**: Dope-Context fix with 3-layer truncation
- **MCP Spec**: No token limit documented (discovered empirically)
- **Claude Code Transport**: 10K hard limit enforced
- **ADHD Design**: Progressive disclosure must be preserved during truncation
