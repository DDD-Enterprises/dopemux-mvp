#!/usr/bin/env python3
"""
Context Relevance Filter Hook
Helps Claude distinguish between task-relevant and task-irrelevant context

This hook runs before major analysis tasks to help maintain focus
on the actual user request rather than getting distracted by 
project-specific details that aren't relevant to the current task.
"""

import json
import sys
from typing import Dict, List, Any

def analyze_task_scope(user_request: str, context_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze whether context information is relevant to the user's actual request
    """
    
    # Extract task keywords from user request
    task_keywords = extract_task_keywords(user_request)
    
    # Categorize context information
    context_categories = {
        "project_specific": ["git_status", "file_contents", "branch_names", "test_files"],
        "tool_specific": ["claude_config", "mcp_servers", "slash_commands", "hooks"],
        "domain_specific": ["privacy", "security", "business_logic", "api_endpoints"],
        "workflow_specific": ["development_process", "quality_gates", "workflows"]
    }
    
    # Determine relevance based on task type
    relevance_map = {
        "integration": ["tool_specific", "workflow_specific"],
        "analysis": ["project_specific", "domain_specific"],
        "workflow": ["workflow_specific", "tool_specific"],
        "setup": ["tool_specific"],
        "enhancement": ["workflow_specific", "tool_specific"]
    }
    
    task_type = determine_task_type(user_request)
    relevant_categories = relevance_map.get(task_type, ["tool_specific"])
    
    return {
        "task_type": task_type,
        "relevant_context": relevant_categories,
        "focus_reminder": f"Stay focused on {task_type} task. Ignore project-specific details unless directly relevant.",
        "warning_signs": ["getting into domain-specific features", "assuming project context", "scope creep"]
    }

def extract_task_keywords(request: str) -> List[str]:
    """Extract key task-oriented words from user request"""
    task_indicators = [
        "integrate", "analysis", "workflow", "setup", "enhance", 
        "improve", "optimize", "configure", "implement", "design"
    ]
    return [word for word in task_indicators if word.lower() in request.lower()]

def determine_task_type(request: str) -> str:
    """Determine the primary task type from user request"""
    if "integrate" in request.lower() or "add" in request.lower():
        return "integration"
    elif "analyze" in request.lower() or "think through" in request.lower():
        return "analysis" 
    elif "workflow" in request.lower() or "process" in request.lower():
        return "workflow"
    elif "setup" in request.lower() or "configure" in request.lower():
        return "setup"
    elif "improve" in request.lower() or "enhance" in request.lower():
        return "enhancement"
    else:
        return "general"

def main():
    """Main hook execution"""
    if len(sys.argv) < 2:
        print("Usage: context_relevance_filter.py '<user_request>'")
        sys.exit(1)
        
    user_request = sys.argv[1]
    
    # Analyze task scope
    analysis = analyze_task_scope(user_request, {})
    
    # Output guidance
    print(json.dumps({
        "type": "context_guidance",
        "analysis": analysis,
        "recommendation": f"Focus on {analysis['task_type']} aspects. Avoid project-specific assumptions."
    }))

if __name__ == "__main__":
    main()