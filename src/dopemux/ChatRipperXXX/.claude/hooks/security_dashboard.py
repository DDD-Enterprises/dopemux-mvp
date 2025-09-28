#!/usr/bin/env python3
"""
Security Dashboard for Smart Hooks Phase 1.2
Displays security decisions, patterns, and adaptive learning results
"""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import Counter

def load_security_audit():
    """Load security audit data"""
    audit_file = ".claude/hooks/data/security_audit.json"
    if os.path.exists(audit_file):
        with open(audit_file, 'r') as f:
            return json.load(f)
    return {"decisions": []}

def show_security_summary():
    """Display security decision summary"""
    audit_data = load_security_audit()
    decisions = audit_data.get("decisions", [])
    
    print("🛡️ ADAPTIVE SECURITY SUMMARY")
    print("=" * 50)
    
    if not decisions:
        print("No security decisions recorded yet.")
        print("Enable with: export HOOKS_ENABLE_ADAPTIVE_SECURITY=1")
        return
    
    # Decision counts
    decision_counter = Counter(d["decision"] for d in decisions)
    total_decisions = len(decisions)
    
    print(f"Total Decisions: {total_decisions}")
    for decision, count in decision_counter.most_common():
        percentage = (count / total_decisions) * 100
        icon = {"allow": "✅", "ask": "⚠️", "deny": "🚫"}.get(decision, "❓")
        print(f"  {icon} {decision.title()}: {count} ({percentage:.1f}%)")
    
    print()
    
    # Recent activity
    recent_decisions = decisions[-10:] if decisions else []
    if recent_decisions:
        print("📊 Recent Security Decisions:")
        for decision in recent_decisions[-5:]:  # Last 5
            timestamp = decision.get("timestamp", "")
            cmd = decision.get("command", "Unknown")[:40]
            dec = decision.get("decision", "unknown")
            risk = decision.get("risk_score", 0)
            
            icon = {"allow": "✅", "ask": "⚠️", "deny": "🚫"}.get(dec, "❓")
            if risk > 0:
                print(f"  {icon} {cmd}... (risk: {risk:.1f})")
            else:
                print(f"  {icon} {cmd}...")
    
    print()

def show_risk_analysis():
    """Display risk analysis and patterns"""
    audit_data = load_security_audit()
    decisions = audit_data.get("decisions", [])
    
    print("📈 SECURITY RISK ANALYSIS")
    print("=" * 50)
    
    if not decisions:
        print("No risk data available yet.")
        return
    
    # Risk score distribution
    risk_decisions = [d for d in decisions if d.get("risk_score", 0) > 0]
    if risk_decisions:
        risk_scores = [d["risk_score"] for d in risk_decisions]
        avg_risk = sum(risk_scores) / len(risk_scores)
        max_risk = max(risk_scores)
        
        print(f"Risk Assessment:")
        print(f"  Average Risk Score: {avg_risk:.2f}")
        print(f"  Maximum Risk Score: {max_risk:.2f}")
        print(f"  High Risk Commands (>0.7): {sum(1 for r in risk_scores if r > 0.7)}")
        print()
    
    # Command patterns
    command_counter = Counter()
    for decision in decisions[-50:]:  # Last 50 decisions
        cmd = decision.get("command", "").split()[0]  # First word
        if cmd:
            command_counter[cmd] += 1
    
    if command_counter:
        print("Most Common Commands:")
        for cmd, count in command_counter.most_common(5):
            print(f"  • {cmd}: {count}x")
    
    print()

def show_learning_status():
    """Display adaptive learning status"""
    print("🧠 ADAPTIVE LEARNING STATUS")  
    print("=" * 50)
    
    # Check if adaptive security is enabled
    adaptive_enabled = os.getenv("HOOKS_ENABLE_ADAPTIVE_SECURITY", "0") == "1"
    print(f"Adaptive Security: {'✅ ENABLED' if adaptive_enabled else '❌ DISABLED'}")
    
    if not adaptive_enabled:
        print("Enable with: export HOOKS_ENABLE_ADAPTIVE_SECURITY=1")
        return
    
    # Load patterns if available
    patterns_file = ".claude/hooks/data/security_patterns.json"
    if os.path.exists(patterns_file):
        with open(patterns_file, 'r') as f:
            patterns = json.load(f)
            legitimate_patterns = patterns.get("legitimate_patterns", [])
            print(f"Learned Patterns: {len(legitimate_patterns)}")
    else:
        print("Learned Patterns: Using defaults")
    
    # Context detection
    context_features = []
    if os.path.exists("pyproject.toml") or os.path.exists("requirements.txt"):
        context_features.append("Python project")
    if os.path.exists("package.json"):
        context_features.append("Node.js project")
    if os.path.exists("Dockerfile"):
        context_features.append("Docker project")
    if os.path.exists(".git"):
        context_features.append("Git repository")
    
    print(f"Context Detection: {', '.join(context_features) if context_features else 'Basic'}")
    
    print()
    
    # Security improvements
    audit_data = load_security_audit()
    decisions = audit_data.get("decisions", [])
    
    if decisions:
        false_positives = sum(1 for d in decisions if d.get("decision") == "ask" and "low risk" in d.get("reason", "").lower())
        learning_decisions = sum(1 for d in decisions if "legitimate pattern" in d.get("reason", "").lower())
        
        print("Learning Improvements:")
        print(f"  Pattern-based Allows: {learning_decisions}")
        print(f"  Potential False Positives: {false_positives}")
        
        if learning_decisions > 0:
            improvement = (learning_decisions / len(decisions)) * 100
            print(f"  Smart Decision Rate: {improvement:.1f}%")

def show_help():
    """Show help information"""
    print("🛡️ Adaptive Security Dashboard - Phase 1.2")
    print("=" * 50)
    print("Usage: python .claude/hooks/security_dashboard.py [option]")
    print()
    print("Options:")
    print("  --summary     Show security decision summary")
    print("  --risk        Show risk analysis and patterns")  
    print("  --learning    Show adaptive learning status")
    print("  --help        Show this help")
    print()
    print("Environment Variables:")
    print("  HOOKS_ENABLE_ADAPTIVE_SECURITY=1  Enable adaptive security")
    print()

def main():
    if len(sys.argv) < 2:
        # Default: show all information
        show_security_summary()
        show_risk_analysis()
        show_learning_status()
    else:
        arg = sys.argv[1].lower()
        if arg in ["--summary", "-s"]:
            show_security_summary()
        elif arg in ["--risk", "-r"]:
            show_risk_analysis()
        elif arg in ["--learning", "-l"]:
            show_learning_status()
        elif arg in ["--help", "-h"]:
            show_help()
        else:
            show_help()

if __name__ == "__main__":
    main()
