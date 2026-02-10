#!/usr/bin/env python3
"""
Claude Code UserPromptSubmit Hook - ADHD Intent Analysis

Intercepts user prompts BEFORE Claude processes them to:
1. Log user intent to ConPort for pattern analysis
2. Inject ADHD context into Claude's processing
3. Detect scope creep / task switching patterns
4. Warn if starting new work with unfinished tasks

Usage:
  Configure in .claude/settings.json:
  {
    "hooks": {
      "UserPromptSubmit": [{
        "command": "python3 .claude/hooks/prompt_analyzer.py",
        "timeout": 3000
      }]
    }
  }
"""
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

# ADHD Engine API endpoint
ADHD_ENGINE_URL = "http://localhost:8080/api/v1"


def _http_json(method: str, url: str, payload: Dict[str, Any] | None = None, timeout: float = 2.0) -> Dict[str, Any] | None:
    """Helper to perform JSON HTTP requests using standard library."""
    try:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        
        req = urllib_request.Request(url, data=data, headers=headers, method=method)
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            if not body:
                return None
            return json.loads(body.decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, ConnectionRefusedError):
        return None


def analyze_prompt(prompt: str) -> Dict[str, bool]:
    """
    Analyze user prompt for ADHD-relevant signals.
    
    Returns dict of detected patterns.
    """
    prompt_lower = prompt.lower()
    
    signals = {
        # Work type detection
        "is_new_feature_request": any(kw in prompt_lower for kw in [
            "new feature", "add", "create", "implement", "build", "make"
        ]),
        "is_bug_fix": any(kw in prompt_lower for kw in [
            "fix", "bug", "broken", "error", "issue", "wrong", "not working"
        ]),
        "is_refactor": any(kw in prompt_lower for kw in [
            "refactor", "clean up", "reorganize", "improve", "optimize"
        ]),
        
        # ADHD pattern detection
        "is_context_switch": any(kw in prompt_lower for kw in [
            "actually", "wait", "instead", "switch to", "forget that",
            "never mind", "hold on", "let's do", "different"
        ]),
        "is_complex_request": (
            len(prompt.split()) > 50 or 
            "and also" in prompt_lower or
            prompt_lower.count(",") > 3
        ),
        "mentions_urgency": any(kw in prompt_lower for kw in [
            "urgent", "asap", "quickly", "fast", "immediately", "now", "hurry"
        ]),
        "is_research_mode": any(kw in prompt_lower for kw in [
            "how do", "what is", "explain", "research", "find out",
            "understand", "learn about", "tell me about"
        ]),
        
        # Potential overwhelm signals
        "is_scope_creep": any(kw in prompt_lower for kw in [
            "and also add", "while you're at it", "one more thing",
            "plus", "in addition", "as well as"
        ]),
        "is_perfectionism": any(kw in prompt_lower for kw in [
            "make it perfect", "polish", "every detail", "flawless",
            "beautiful", "amazing", "impressive"
        ]),
        "is_decision_avoidance": any(kw in prompt_lower for kw in [
            "i don't know", "maybe", "not sure", "whatever you think",
            "you decide", "any of these"
        ]),
    }
    
    return signals


def get_adhd_context() -> Dict[str, Any]:
    """Get current ADHD state for context injection."""
    data = _http_json("GET", f"{ADHD_ENGINE_URL}/state", timeout=2)
    if isinstance(data, dict):
        return data
    
    return {
        "energy": "unknown",
        "attention": "unknown", 
        "session_minutes": 0
    }


def check_unfinished_work() -> Dict[str, Any]:
    """Check for unfinished work that might conflict."""
    data = _http_json("GET", f"{ADHD_ENGINE_URL}/unfinished-work", timeout=2)
    if isinstance(data, dict):
        return data
    
    return {"count": 0, "items": []}


def log_intent(prompt_summary: str, signals: Dict, adhd_state: Dict):
    """Log intent to ADHD Engine (non-blocking)."""
    _http_json("POST", f"{ADHD_ENGINE_URL}/log-intent", payload={
        "prompt_summary": prompt_summary,
        "signals": signals,
        "adhd_state": adhd_state,
        "timestamp": datetime.now().isoformat()
    }, timeout=1)


def save_context_on_switch(prompt_hint: str):
    """Trigger context save on detected switch."""
    _http_json("POST", f"{ADHD_ENGINE_URL}/save-context", payload={
        "reason": "context_switch_detected",
        "prompt_hint": prompt_hint[:50]
    }, timeout=1)


def build_context_injection(
    signals: Dict[str, bool],
    adhd_state: Dict[str, Any],
    unfinished: Dict[str, Any]
) -> List[str]:
    """Build contextual messages to inject into Claude's processing."""
    context_lines = []
    
    # Warn about starting new work with many unfinished items
    unfinished_count = unfinished.get("count", 0)
    if signals["is_new_feature_request"] and unfinished_count > 5:
        context_lines.append(
            f"⚠️ User has {unfinished_count} unfinished items. "
            "Consider asking if they want to complete existing work first."
        )
    
    # Warn about complex requests during low energy
    if signals["is_complex_request"] and adhd_state.get("energy") == "low":
        context_lines.append(
            "⚠️ Complex request during low energy. "
            "Consider breaking into smaller chunks and tackling the simplest first."
        )
    
    # Flag scope creep
    if signals["is_scope_creep"]:
        context_lines.append(
            "📝 Scope creep detected. Consider focusing on the core request first, "
            "then addressing additions in follow-up prompts."
        )
    
    # Flag context switching
    if signals["is_context_switch"]:
        context_lines.append(
            "📝 Context switch detected. Current context breadcrumb auto-saved."
        )
    
    # Research spiral warning
    if signals["is_research_mode"] and adhd_state.get("session_minutes", 0) > 30:
        context_lines.append(
            "💡 Extended research session. Consider setting a specific output goal "
            "to prevent research rabbit hole."
        )
    
    # Decision avoidance support
    if signals["is_decision_avoidance"]:
        context_lines.append(
            "🤔 Decision uncertainty detected. Consider using Pal consensus "
            "for structured multi-perspective analysis."
        )
    
    # Urgency bias check
    if signals["mentions_urgency"]:
        context_lines.append(
            "⏰ Urgency mentioned. Verify this is truly urgent - "
            "ADHD can make everything feel urgent. What's the actual deadline?"
        )
    
    return context_lines


def main():
    """Main hook entry point."""
    try:
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)
        user_prompt = hook_input.get("prompt", "")
        
        if not user_prompt:
            # No prompt, allow through
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)
        
        # Analyze the prompt
        signals = analyze_prompt(user_prompt)
        adhd_state = get_adhd_context()
        unfinished = check_unfinished_work()
        
        # Log intent (non-blocking)
        log_intent(
            prompt_summary=user_prompt[:100],
            signals=signals,
            adhd_state=adhd_state
        )
        
        # Handle context switch
        if signals["is_context_switch"]:
            save_context_on_switch(user_prompt)
        
        # Build context injection
        context_lines = build_context_injection(signals, adhd_state, unfinished)
        
        # Build output
        output = {
            "decision": "allow",
            "metadata": {
                "adhd_signals": signals,
                "energy_level": adhd_state.get("energy"),
                "attention_state": adhd_state.get("attention"),
                "unfinished_count": unfinished.get("count", 0)
            }
        }
        
        # Add context injection if we have messages
        if context_lines:
            output["contextInjection"] = "\n".join(context_lines)
        
        print(json.dumps(output))
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Invalid input, allow through
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    except Exception as e:
        # On error, allow through but log
        print(json.dumps({
            "decision": "allow",
            "metadata": {"error": str(e)}
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()

