#!/usr/bin/env python3
"""
Token Usage Dashboard for Smart Hooks Phase 1.1
Displays current session usage, patterns, and optimization opportunities
"""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import Counter

def load_patterns():
    """Load usage patterns from storage"""
    patterns_file = ".claude/hooks/data/usage_patterns.json"
    if os.path.exists(patterns_file):
        with open(patterns_file, 'r') as f:
            return json.load(f)
    return {"sessions": []}

def load_session_metrics():
    """Load session metrics"""
    metrics_file = ".claude/hooks/data/session_metrics.json"
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            return json.load(f)
    return {"current_session": {"current_usage": 0, "tool_calls": []}}

def format_tokens(tokens):
    """Format token count for display"""
    if tokens >= 1000:
        return f"{tokens/1000:.1f}k"
    return str(tokens)

def show_current_usage():
    """Display current session usage"""
    metrics = load_session_metrics()
    current = metrics.get("current_session", {})
    
    print("🔥 CURRENT SESSION USAGE")
    print("=" * 50)
    
    usage = current.get("current_usage", 0)
    budget = current.get("token_budget", 200000)
    percentage = (usage / budget) * 100
    
    print(f"Token Usage: {format_tokens(usage)} / {format_tokens(budget)} ({percentage:.1f}%)")
    
    # Visual progress bar
    bar_width = 30
    filled = int((usage / budget) * bar_width)
    bar = "█" * filled + "░" * (bar_width - filled)
    
    if percentage < 50:
        status = "🟢 GOOD"
    elif percentage < 80:
        status = "🟡 MODERATE"
    else:
        status = "🔴 HIGH"
    
    print(f"Progress: [{bar}] {status}")
    print()
    
    # Recent tool calls
    tool_calls = current.get("tool_calls", [])
    if tool_calls:
        print("📊 Recent Tool Usage:")
        for call in tool_calls[-5:]:  # Last 5 calls
            tokens = format_tokens(call.get("tokens", 0))
            tool = call.get("tool", "Unknown")
            print(f"  • {tool}: {tokens} tokens")
    print()

def show_patterns():
    """Display usage patterns"""
    patterns = load_patterns()
    sessions = patterns.get("sessions", [])
    
    if not sessions:
        print("📈 No patterns recorded yet")
        print("Enable with: export HOOKS_ENABLE_SMART_OPTIMIZATION=1")
        return
    
    print("📈 USAGE PATTERNS")
    print("=" * 50)
    
    # Tool frequency
    tool_counter = Counter()
    token_usage = {}
    
    for session in sessions[-50:]:  # Last 50 records
        tool = session.get("tool", "Unknown")
        tokens = session.get("estimated_tokens", 0)
        
        tool_counter[tool] += 1
        if tool not in token_usage:
            token_usage[tool] = []
        token_usage[tool].append(tokens)
    
    print("Most Used Tools:")
    for tool, count in tool_counter.most_common(5):
        avg_tokens = sum(token_usage[tool]) // len(token_usage[tool])
        print(f"  • {tool}: {count}x (avg {format_tokens(avg_tokens)} tokens)")
    
    print()

def show_optimization_suggestions():
    """Display optimization opportunities"""
    patterns = load_patterns()
    sessions = patterns.get("sessions", [])
    
    print("💡 OPTIMIZATION SUGGESTIONS")
    print("=" * 50)
    
    suggestions = []
    
    # Analyze recent sessions for optimization opportunities
    recent_sessions = sessions[-20:] if sessions else []
    
    for session in recent_sessions:
        tool = session.get("tool", "")
        tool_input = session.get("input", {})
        tokens = session.get("estimated_tokens", 0)
        
        # High token usage tools
        if tokens > 10000:
            if "task-master-ai" in tool and "get_tasks" in tool:
                if not tool_input.get("status"):
                    suggestions.append("🎯 Use status=pending with TaskMaster get_tasks to save ~15k tokens")
            
            if "conport" in tool and not any(k in tool_input for k in ("limit", "top_k")):
                suggestions.append("🎯 Add limit=3-5 to ConPort queries to save ~10k tokens")
            
            if "zen" in tool:
                files = tool_input.get("files", [])
                if len(files) > 1:
                    suggestions.append("🎯 Limit Zen files to 1 to save ~20k tokens")
    
    # Remove duplicates
    unique_suggestions = list(set(suggestions))
    
    if unique_suggestions:
        for suggestion in unique_suggestions[:5]:  # Top 5
            print(f"  {suggestion}")
    else:
        print("  ✅ No obvious optimizations found")
    
    print()
    
    # Token savings potential
    if sessions:
        total_tokens = sum(s.get("estimated_tokens", 0) for s in recent_sessions)
        print(f"Recent Usage: {format_tokens(total_tokens)} tokens")
        print(f"Optimization Potential: ~{format_tokens(total_tokens * 0.3)} tokens (30% savings)")

def show_help():
    """Show help information"""
    print("🚀 Smart Hooks Dashboard - Phase 1.1")
    print("=" * 50)
    print("Usage: python .claude/hooks/dashboard.py [option]")
    print()
    print("Options:")
    print("  --current     Show current session usage")
    print("  --patterns    Show usage patterns")
    print("  --suggestions Show optimization suggestions")
    print("  --help        Show this help")
    print()
    print("Environment Variables:")
    print("  HOOKS_ENABLE_SMART_OPTIMIZATION=1  Enable pattern tracking")
    print()

def main():
    if len(sys.argv) < 2:
        # Default: show all information
        show_current_usage()
        show_patterns()
        show_optimization_suggestions()
    else:
        arg = sys.argv[1].lower()
        if arg in ["--current", "-c"]:
            show_current_usage()
        elif arg in ["--patterns", "-p"]:
            show_patterns()
        elif arg in ["--suggestions", "-s"]:
            show_optimization_suggestions()
        elif arg in ["--help", "-h"]:
            show_help()
        else:
            show_help()

if __name__ == "__main__":
    main()
