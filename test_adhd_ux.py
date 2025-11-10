#!/usr/bin/env python3
"""
Test ADHD UX improvements for Phase 3.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dopemux.adhd.workflow_manager import ADHDWorkflowManager
from dopemux.ux.progress_display import ProgressDisplay
from dopemux.ux.interactive_prompts import InteractivePrompts

async def test_adhd_ux():
    """Test ADHD UX components."""
    print("🧠 Testing ADHD UX Improvements...")

    # Test 1: Workflow Manager
    print("\n📋 Testing Workflow Manager...")
    manager = ADHDWorkflowManager()

    # Start session
    session = manager.start_session("Testing ADHD UX")
    print(f"Session started: {session['session_id']}")

    # Update load
    manager.update_cognitive_load(0.8, "High complexity testing")
    print(f"Current focus level: {manager.current_focus_level}")

    # Check break
    break_needed, reason = manager.check_break_needed()
    print(f"Break needed: {break_needed} ({reason})")

    # End session
    summary = manager.end_session()
    print(f"Session summary: {summary['duration_minutes']:.1f} min")

    # Test 2: Progress Display
    print("\n📊 Testing Progress Display...")
    display = ProgressDisplay()

    # Show operation start
    display.show_operation_start("Test operation", total_steps=5, complexity=0.6)
    print("Progress display initiated")

    # Show completion
    display.show_operation_complete("Test operation", duration=2.5, success=True)
    print("Completion display shown")

    # Test 3: Interactive Prompts
    print("\n🤔 Testing Interactive Prompts...")
    prompts = InteractivePrompts()

    # Test action selection
    actions = [
        {"name": "Option 1", "description": "Simple action", "complexity": 0.3},
        {"name": "Option 2", "description": "Moderate action", "complexity": 0.6},
        {"name": "Option 3", "description": "Complex action", "complexity": 0.8}
    ]
    selection = prompts.ask_action_selection(actions, "Choose an action")
    print(f"Selection: {selection}")

    print("\n🎉 ADHD UX tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_adhd_ux())