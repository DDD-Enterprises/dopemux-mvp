#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime

# Configuration
DISABLE_NETWORK = os.getenv("HOOKS_DISABLE_NETWORK", "1") == "1"
BLOCK_SUDO = os.getenv("HOOKS_BLOCK_SUDO", "1") == "1"
BLOCK_RM = os.getenv("HOOKS_BLOCK_RM", "1") == "1"
ADAPTIVE_SECURITY = os.getenv("HOOKS_ENABLE_ADAPTIVE_SECURITY", "0") == "1"
DEV_MODE = os.getenv("HOOKS_DEV_MODE", "0") == "1"
SENSITIVE_PATH_PATTERNS = [r"/?\.env($|[\./])", r"/secrets/", r"/?\.aws/"]
ALLOWLIST_CMDS = set(filter(None, os.getenv("HOOKS_ALLOWLIST_CMDS", "").split(",")))

def out(decision, reason): 
    print(json.dumps({"decision": decision, "permissionDecisionReason": reason}), flush=True)

def is_sensitive(path: str) -> bool:
    low = (path or "").lower()
    for pat in SENSITIVE_PATH_PATTERNS:
        if re.search(pat, low): return True
    return False

def build_context():
    """Build context for adaptive security decisions - Phase 1.2"""
    context = {}
    
    # Project type detection
    if os.path.exists("pyproject.toml") or os.path.exists("requirements.txt"):
        context["project_type"] = "python"
    elif os.path.exists("package.json"):
        context["project_type"] = "nodejs" 
    elif os.path.exists("Dockerfile"):
        context["project_type"] = "docker"
    elif os.path.exists("Cargo.toml"):
        context["project_type"] = "rust"
    else:
        context["project_type"] = "unknown"
    
    # Git context
    context["git_repository"] = os.path.exists(".git")
    
    return context

def evaluate_adaptive_security(command, context):
    """Smart security evaluation - Phase 1.2"""
    if not ADAPTIVE_SECURITY:
        return None, None, 0.0
    
    command_lower = command.lower().strip()
    
    # Calculate base risk
    risk_score = 0.0
    risk_factors = {
        r'(^|\s)sudo(\s|$)': 0.9,
        r'(^|\s)rm(\s|-rf)': 0.8,
        r'(curl|wget).*\|\s*(bash|sh)': 0.9,
        r'pip\s+install(?!\s+-r)': 0.5,
        r'npm\s+install(?!\s*$)': 0.5,
        r'chmod.*7': 0.7,
        r'(^|\s)(ls|cat|git|python)(\s|$)': 0.1
    }
    
    for pattern, risk in risk_factors.items():
        if re.search(pattern, command_lower):
            risk_score = max(risk_score, risk)
    
    # Context adjustments
    project_type = context.get("project_type", "unknown")
    if project_type == "docker" and "docker" in command_lower:
        risk_score -= 0.2  # Lower risk in Docker projects
    
    if project_type in ["python", "nodejs"] and "install" in command_lower:
        # Check for package file modifications (simplified)
        if any(os.path.exists(f) for f in ["requirements.txt", "package.json", "pyproject.toml"]):
            risk_score -= 0.1  # Lower risk if package files exist
    
    # Decision logic - FIXED: Proper range handling
    if risk_score < 0.2:
        return "allow", f"✅ Low risk operation (risk: {risk_score:.1f})", 0.9
    elif risk_score < 0.8:  # FIXED: Changed from < 0.5 to < 0.8 to include 0.5-0.7 range
        return "ask", f"⚠️ Moderate risk operation (risk: {risk_score:.1f}) | Project: {project_type}", 0.7
    else:
        return "deny", f"🚫 High risk operation blocked (risk: {risk_score:.1f})", 0.8

def record_security_decision(command, decision, reason, risk_score=0.0):
    """Record security decisions for learning - Phase 1.2"""
    if not ADAPTIVE_SECURITY:
        return
        
    try:
        data_dir = ".claude/hooks/data"
        os.makedirs(data_dir, exist_ok=True)
        
        audit_file = os.path.join(data_dir, "security_audit.json")
        
        # Load existing audit
        audit_data = {"decisions": []}
        if os.path.exists(audit_file):
            with open(audit_file, 'r') as f:
                audit_data = json.load(f)
        
        # Add new record
        record = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "decision": decision,
            "reason": reason,
            "risk_score": risk_score
        }
        
        audit_data["decisions"].append(record)
        audit_data["last_updated"] = record["timestamp"]
        
        # Keep last 200 records
        if len(audit_data["decisions"]) > 200:
            audit_data["decisions"] = audit_data["decisions"][-200:]
        
        # Save audit
        with open(audit_file, 'w') as f:
            json.dump(audit_data, f, indent=2)
            
    except:
        pass  # Silent fail

def check_legitimate_patterns(command):
    """Check against known legitimate patterns - Phase 1.2"""
    if not ADAPTIVE_SECURITY:
        return False
        
    # Common legitimate development patterns - FIXED: More inclusive patterns
    legitimate_patterns = [
        r'^git\s+(status|add|commit|push|pull|diff|log|branch)',  # Added more git commands
        r'^python\s+-m\s+(pytest|pip|mypy|ruff)',
        r'^npm\s+(test|run|start|install)',
        r'^docker\s+(build|run|ps|stop|rm)',
        r'^ls\s|^cat\s|^head\s|^tail\s',
        r'^mkdir\s+[^/]',  # Local directories only
        r'^cp\s+[^/].*[^/]',  # Local file operations
        r'^cd\s+[^/]'  # Local directory changes
    ]
    
    command_lower = command.lower().strip()
    for pattern in legitimate_patterns:
        if re.match(pattern, command_lower):
            return True
    
    return False

def main():
    # Development mode bypass - allows smooth development workflow
    if DEV_MODE:
        out("allow", "🚀 Development mode - bypassing security restrictions")
        return
        
    try: 
        data = json.loads(sys.stdin.read() or "{}")
    except Exception: 
        data = {}
    
    if (data.get("event") or data.get("eventName")) != "PreToolUse": 
        return
    
    tool = (data.get("tool") or data.get("toolName") or "").lower()
    ti = data.get("toolInput") or data.get("input") or {}
    
    # Build context for adaptive security
    context = build_context()
    
    # Handle bash/shell commands
    if tool in {"bash","terminal","shell","execute","run","sh"}:
        cmd = (ti.get("command") or ti.get("cmd") or "").strip()
        low = cmd.lower()
        
        # Check allowlist first
        if cmd in ALLOWLIST_CMDS: 
            record_security_decision(cmd, "allow", f"Allowed: {cmd}")
            out("allow", f"✅ Allowlisted: {cmd}")
            return
        
        # Check legitimate patterns
        if check_legitimate_patterns(cmd):
            record_security_decision(cmd, "allow", "Legitimate development pattern", 0.1)
            out("allow", f"✅ Legitimate pattern: {cmd[:50]}...")
            return
        
        # Adaptive security evaluation
        adaptive_decision, adaptive_reason, confidence = evaluate_adaptive_security(cmd, context)
        if adaptive_decision:
            record_security_decision(cmd, adaptive_decision, adaptive_reason, confidence)
            out(adaptive_decision, adaptive_reason)
            return
        
        # Fallback to original security rules
        if BLOCK_SUDO and re.search(r"(^|\s)sudo(\s|$)", low): 
            record_security_decision(cmd, "deny", "'sudo' not permitted")
            out("deny","🚫 'sudo' not permitted."); return
            
        if BLOCK_RM and re.search(r"(^|\s)rm(\s|-)", low): 
            record_security_decision(cmd, "ask", "'rm' detected - destructive action")
            out("ask","⚠️ 'rm' detected. Confirm destructive action."); return
            
        if DISABLE_NETWORK and any(w in low for w in ["curl ","wget ","pip install","npm install"]):
            record_security_decision(cmd, "ask", "Network install detected")
            out("ask","⚠️ Network installs disabled by default. Confirm or use a lockfile."); return
    
    # Handle file operations
    elif tool in {"read","readfile","read_file"}:
        p = (ti.get("file_path") or ti.get("path") or "").strip()
        if p and is_sensitive(p): 
            record_security_decision(f"read {p}", "deny", f"Sensitive file access: {p}")
            out("deny", f"🚫 Reading sensitive file '{p}' not permitted."); return
            
    elif tool in {"write","writefile","write_file"}:
        p = (ti.get("file_path") or ti.get("path") or "").strip()
        content = (ti.get("content") or "")
        
        if p.endswith(("package.json","pyproject.toml","requirements.txt","poetry.lock")):
            record_security_decision(f"write {p}", "ask", "Dependency manifest change")
            out("ask","⚠️ Dependency manifest change detected. Confirm rationale."); return
            
        if len(content) > 200_000: 
            record_security_decision(f"write {p}", "ask", f"Large write {len(content)} bytes")
            out("ask","⚠️ Large write (>200KB). Confirm intent."); return
    
    # Default allow with logging
    record_security_decision(f"{tool}", "allow", "Default allow")

if __name__ == "__main__": 
    main()
