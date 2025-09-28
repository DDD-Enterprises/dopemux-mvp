#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

# Configuration
CONPORT_STRICT = os.getenv("HOOKS_CONPORT_STRICT", "1") == "1"
EXA_MIN_QUERY_LEN = int(os.getenv("HOOKS_EXA_MIN_QUERY_LEN", "3"))
CLAUDE_CONTEXT_MAX_RESULTS = int(os.getenv("HOOKS_CLAUDE_CONTEXT_MAX_RESULTS", "3"))
TASKMASTER_DEFAULT_LIMIT = int(os.getenv("HOOKS_TASKMASTER_LIMIT", "3"))
ZEN_MAX_FILES = int(os.getenv("HOOKS_ZEN_MAX_FILES", "1"))
SMART_OPTIMIZATION = os.getenv("HOOKS_ENABLE_SMART_OPTIMIZATION", "0") == "1"
DEV_MODE = os.getenv("HOOKS_DEV_MODE", "0") == "1"
GENERIC_TERMS = {"help","docs","documentation","fix","error","issue","bug","search"}

def out(decision, reason): 
    print(json.dumps({"decision": decision, "permissionDecisionReason": reason}), flush=True)

def record_usage(tool_name, tool_input, decision, reason):
    """Record tool usage for pattern analysis - Smart Hooks Phase 1.1"""
    if not SMART_OPTIMIZATION:
        return
        
    try:
        data_dir = ".claude/hooks/data"
        os.makedirs(data_dir, exist_ok=True)
        
        patterns_file = os.path.join(data_dir, "usage_patterns.json")
        
        # Load existing patterns
        patterns = {"sessions": [], "last_updated": None}
        if os.path.exists(patterns_file):
            with open(patterns_file, 'r') as f:
                patterns = json.load(f)
        
        # Estimate tokens
        tokens = estimate_token_usage(tool_name, tool_input)
        
        # Add new record
        record = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "input": tool_input,
            "decision": decision,
            "reason": reason,
            "estimated_tokens": tokens
        }
        
        patterns["sessions"].append(record)
        patterns["last_updated"] = record["timestamp"]
        
        # Keep last 200 records to prevent unbounded growth
        if len(patterns["sessions"]) > 200:
            patterns["sessions"] = patterns["sessions"][-200:]
        
        # Save patterns
        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)
            
    except:
        pass  # Silent fail - don't break hook execution

def estimate_token_usage(tool_name, tool_input):
    """Estimate token usage for different MCP tools"""
    tool_lower = tool_name.lower()
    
    # High token usage tools
    if "zen" in tool_lower:
        return 29000
    elif "task-master-ai" in tool_lower:
        if tool_input.get("status") or tool_input.get("withSubtasks") == False:
            return 1500  # Filtered
        return 6000  # Unfiltered
    elif "conport" in tool_lower:
        if any(k in tool_input for k in ("limit", "top_k", "limit_per_type")):
            return 3000  # Limited
        return 17000  # Full context
    elif "serena" in tool_lower:
        return 15000
    elif "claude-context" in tool_lower or "claude_context" in tool_lower:
        return 5000
    elif "exa" in tool_lower:
        return 3000
    elif "fast-markdown" in tool_lower:
        return 1000
    elif "openmemory" in tool_lower:
        return 500
    elif "cli" in tool_lower:
        return 200
    
    return 1000  # Default

def get_smart_suggestions(tool_name, tool_input):
    """Generate smart optimization suggestions"""
    suggestions = []
    
    if "task-master-ai" in tool_name and "get_tasks" in tool_name:
        if not tool_input.get("status") and tool_input.get("withSubtasks") != False:
            suggestions.append("💡 Add status=pending + withSubtasks=false to save ~15k tokens")
    
    if "conport" in tool_name and not any(k in tool_input for k in ("limit", "top_k")):
        suggestions.append("💡 Add limit=3-5 to reduce ConPort token usage")
    
    if "zen" in tool_name:
        files = tool_input.get("files", [])
        if len(files) > 1:
            suggestions.append("💡 Limit Zen files to 1 for token efficiency")
        if not tool_input.get("continuation_id"):
            suggestions.append("💡 Use continuation_id for Zen conversations")
    
    return suggestions

def main():
    # Development mode bypass - allows smooth development workflow
    if DEV_MODE:
        out("allow", "🚀 Development mode - bypassing token restrictions")
        return
        
    try: 
        data = json.loads(sys.stdin.read() or "{}")
    except Exception: 
        data = {}
    
    if (data.get("event") or data.get("eventName")) != "PreToolUse": 
        return
    
    tool = (data.get("tool") or data.get("toolName") or "").lower()
    ti = data.get("toolInput") or data.get("input") or {}
    
    decision = "allow"
    reason = "Token budget check passed"
    
    # ConPort strict mode checks
    if "conport" in tool and CONPORT_STRICT:
        if "get_active_context" in tool: 
            decision, reason = "ask", "Use ConPort summaries or search with small limits before full context."
        elif not any(k in ti for k in ("limit","limit_per_type","top_k")) and any(x in tool for x in ("search_","get_decisions","get_progress","get_custom_data")):
            decision, reason = "ask", "Provide a small 'limit' (3–5) for ConPort reads."
    
    # Exa query validation
    elif "exa" in tool:
        q = (ti.get("query") or (ti.get("q") or "")).strip()
        if len(q) < EXA_MIN_QUERY_LEN or q.lower() in GENERIC_TERMS:
            decision, reason = "ask", "Exa query too broad. Refine (lib, function, error text)."
    
    # Claude Context limits
    elif "claude-context" in tool or "claude_context" in tool:
        max_results = int(ti.get("max_results") or ti.get("limit") or 10)
        if max_results > CLAUDE_CONTEXT_MAX_RESULTS:
            decision, reason = "ask", f"Reduce Claude-Context results to ≤ {CLAUDE_CONTEXT_MAX_RESULTS}."
    
    # TaskMaster optimization
    elif "task-master-ai" in tool:
        if "get_tasks" in tool:
            # Block unlimited task dumps - require filtering
            if not ti.get("status") and ti.get("withSubtasks") != False:
                decision, reason = "ask", "Use status filter (pending/done) or withSubtasks=false for TaskMaster."
            # For unfiltered queries, enforce reasonable limits
            elif not any(k in ti for k in ("status", "withSubtasks")) and not ti.get("limit"):
                decision, reason = "ask", f"Add status filter or limit≤{TASKMASTER_DEFAULT_LIMIT} for TaskMaster queries."
    
    # Zen optimization
    elif "zen" in tool:
        files = ti.get("files", [])
        if len(files) > ZEN_MAX_FILES:
            decision, reason = "ask", f"Limit Zen context files to ≤{ZEN_MAX_FILES} for token efficiency."
        # Encourage continuation_id reuse for long conversations
        elif not ti.get("continuation_id") and len(ti.get("prompt", "")) > 200:
            decision, reason = "ask", "Use continuation_id for long Zen conversations to reduce context."
    
    # Record usage for pattern analysis (Smart Hooks Phase 1.1)
    record_usage(tool, ti, decision, reason)
    
    # Add smart suggestions to reason if enabled
    if SMART_OPTIMIZATION and decision == "allow":
        suggestions = get_smart_suggestions(tool, ti)
        if suggestions:
            reason += " | " + " | ".join(suggestions)
    
    out(decision, reason)

if __name__ == "__main__": 
    main()
