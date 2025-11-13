#!/usr/bin/env python3
"""
Import Phase 1 Tasks to ConPort

Imports the 20 Architecture 3.0 Phase 1 implementation tasks into ConPort
with full ADHD metadata, dependencies, and linking.

Usage:
    python scripts/import-phase1-tasks-to-conport.py

Requirements:
    - ConPort MCP server running
    - Access to ConPort via Python client or MCP tools
"""

import json
import sys
from pathlib import Path

# Phase 1 Tasks with ADHD Metadata
PHASE1_TASKS = [
    # Component 1: Dependency Audit (4 hours)
    {
        "task_id": "1.1",
        "description": "Inventory External Dependencies",
        "full_description": "Task 1.1: Inventory External Dependencies | Duration: 45m | Complexity: 0.4 | Energy: Medium | Audit Task-Orchestrator dependencies (Python packages, services, env vars)",
        "duration_minutes": 45,
        "complexity_score": 0.4,
        "energy_required": "medium",
        "cognitive_load": 0.4,
        "component": "Dependency Audit",
        "dependencies": [],
        "tags": ["phase-1", "audit", "dependencies", "component-1"]
    },
    {
        "task_id": "1.2",
        "description": "Verify Redis Infrastructure",
        "full_description": "Task 1.2: Verify Redis Infrastructure | Duration: 30m | Complexity: 0.3 | Energy: Low | Ensure Redis is running and properly configured",
        "duration_minutes": 30,
        "complexity_score": 0.3,
        "energy_required": "low",
        "cognitive_load": 0.3,
        "component": "Dependency Audit",
        "dependencies": ["1.1"],
        "tags": ["phase-1", "audit", "redis", "component-1"]
    },
    {
        "task_id": "1.3",
        "description": "Audit ConPort API Usage",
        "full_description": "Task 1.3: Audit ConPort API Usage | Duration: 90m | Complexity: 0.6 | Energy: High | Find all ConPort API calls and schema expectations in Task-Orchestrator code",
        "duration_minutes": 90,
        "complexity_score": 0.6,
        "energy_required": "high",
        "cognitive_load": 0.6,
        "component": "Dependency Audit",
        "dependencies": [],
        "tags": ["phase-1", "audit", "conport-api", "component-1"]
    },
    {
        "task_id": "1.4",
        "description": "Check Deployment Infrastructure",
        "full_description": "Task 1.4: Check Deployment Infrastructure | Duration: 45m | Complexity: 0.4 | Energy: Medium | Verify Docker configs, env setup, CI/CD integration",
        "duration_minutes": 45,
        "complexity_score": 0.4,
        "energy_required": "medium",
        "cognitive_load": 0.4,
        "component": "Dependency Audit",
        "dependencies": ["1.1"],
        "tags": ["phase-1", "audit", "deployment", "component-1"]
    },
    {
        "task_id": "1.5",
        "description": "Create Audit Summary",
        "full_description": "Task 1.5: Create Audit Summary | Duration: 30m | Complexity: 0.3 | Energy: Low | Synthesize audit findings and create go/no-go recommendation",
        "duration_minutes": 30,
        "complexity_score": 0.3,
        "energy_required": "low",
        "cognitive_load": 0.3,
        "component": "Dependency Audit",
        "dependencies": ["1.1", "1.2", "1.3", "1.4"],
        "tags": ["phase-1", "audit", "summary", "component-1"]
    },
    # Component 2: Data Contract Adapters (6 hours)
    {
        "task_id": "2.1",
        "description": "Design ConPort Event Schema",
        "full_description": "Task 2.1: Design ConPort Event Schema | Duration: 60m | Complexity: 0.7 | Energy: High | Define event schemas for ConPort → Task-Orchestrator communication",
        "duration_minutes": 60,
        "complexity_score": 0.7,
        "energy_required": "high",
        "cognitive_load": 0.7,
        "component": "Data Contract Adapters",
        "dependencies": ["1.3"],
        "tags": ["phase-1", "adapters", "schema-design", "component-2"]
    },
    {
        "task_id": "2.2",
        "description": "Create ConPort Event Adapter",
        "full_description": "Task 2.2: Create ConPort Event Adapter | Duration: 90m | Complexity: 0.7 | Energy: High | Build adapter class that converts ConPort events to OrchestrationTask",
        "duration_minutes": 90,
        "complexity_score": 0.7,
        "energy_required": "high",
        "cognitive_load": 0.7,
        "component": "Data Contract Adapters",
        "dependencies": ["2.1"],
        "tags": ["phase-1", "adapters", "event-adapter", "component-2"]
    },
    {
        "task_id": "2.3",
        "description": "Create Insight Publisher",
        "full_description": "Task 2.3: Create Insight Publisher | Duration: 60m | Complexity: 0.6 | Energy: High | Build publisher that sends Task-Orchestrator insights to ConPort",
        "duration_minutes": 60,
        "complexity_score": 0.6,
        "energy_required": "high",
        "cognitive_load": 0.6,
        "component": "Data Contract Adapters",
        "dependencies": ["2.1"],
        "tags": ["phase-1", "adapters", "insight-publisher", "component-2"]
    },
    {
        "task_id": "2.4",
        "description": "Implement Schema Mapping",
        "full_description": "Task 2.4: Implement Schema Mapping | Duration: 45m | Complexity: 0.5 | Energy: Medium | Create bidirectional mapping utilities (ConPort ↔ OrchestrationTask)",
        "duration_minutes": 45,
        "complexity_score": 0.5,
        "energy_required": "medium",
        "cognitive_load": 0.5,
        "component": "Data Contract Adapters",
        "dependencies": ["2.2"],
        "tags": ["phase-1", "adapters", "schema-mapping", "component-2"]
    },
    {
        "task_id": "2.5",
        "description": "Remove Direct Storage",
        "full_description": "Task 2.5: Remove Direct Storage | Duration: 75m | Complexity: 0.7 | Energy: High | Replace self.orchestrated_tasks dict with ConPort queries (authority compliance)",
        "duration_minutes": 75,
        "complexity_score": 0.7,
        "energy_required": "high",
        "cognitive_load": 0.7,
        "component": "Data Contract Adapters",
        "dependencies": ["2.2", "2.3"],
        "tags": ["phase-1", "adapters", "refactoring", "component-2", "critical"]
    },
    {
        "task_id": "2.6",
        "description": "Integration Test Event Flow",
        "full_description": "Task 2.6: Integration Test Event Flow | Duration: 50m | Complexity: 0.6 | Energy: High | Test complete event flow (ConPort → Task-Orchestrator → ConPort)",
        "duration_minutes": 50,
        "complexity_score": 0.6,
        "energy_required": "high",
        "cognitive_load": 0.6,
        "component": "Data Contract Adapters",
        "dependencies": ["2.2", "2.3", "2.5"],
        "tags": ["phase-1", "adapters", "testing", "component-2"]
    },
    # Component 3: DopeconBridge Wiring (4 hours)
    {
        "task_id": "3.1",
        "description": "Configure DopeconBridge",
        "full_description": "Task 3.1: Configure DopeconBridge | Duration: 60m | Complexity: 0.6 | Energy: Medium | Set up DopeconBridge routing for Task-Orchestrator",
        "duration_minutes": 60,
        "complexity_score": 0.6,
        "energy_required": "medium",
        "cognitive_load": 0.6,
        "component": "DopeconBridge Wiring",
        "dependencies": [],
        "tags": ["phase-1", "bridge", "configuration", "component-3"]
    },
    {
        "task_id": "3.2",
        "description": "Implement Event Subscription",
        "full_description": "Task 3.2: Implement Event Subscription | Duration: 75m | Complexity: 0.7 | Energy: High | Enable Task-Orchestrator to receive ConPort events via DopeconBridge",
        "duration_minutes": 75,
        "complexity_score": 0.7,
        "energy_required": "high",
        "cognitive_load": 0.7,
        "component": "DopeconBridge Wiring",
        "dependencies": ["3.1", "2.2"],
        "tags": ["phase-1", "bridge", "subscription", "component-3", "critical"]
    },
    {
        "task_id": "3.3",
        "description": "Implement Insight Publishing",
        "full_description": "Task 3.3: Implement Insight Publishing | Duration: 60m | Complexity: 0.6 | Energy: Medium | Enable Task-Orchestrator to send insights back to ConPort",
        "duration_minutes": 60,
        "complexity_score": 0.6,
        "energy_required": "medium",
        "cognitive_load": 0.6,
        "component": "DopeconBridge Wiring",
        "dependencies": ["3.1", "2.3"],
        "tags": ["phase-1", "bridge", "publishing", "component-3"]
    },
    {
        "task_id": "3.4",
        "description": "Test Bridge Communication",
        "full_description": "Task 3.4: Test Bridge Communication | Duration: 45m | Complexity: 0.5 | Energy: Medium | Validate bidirectional DopeconBridge communication",
        "duration_minutes": 45,
        "complexity_score": 0.5,
        "energy_required": "medium",
        "cognitive_load": 0.5,
        "component": "DopeconBridge Wiring",
        "dependencies": ["3.2", "3.3"],
        "tags": ["phase-1", "bridge", "testing", "component-3"]
    },
    # Component 4: Core Module Activation (4 hours)
    {
        "task_id": "4.1",
        "description": "Enable Dependency Analysis",
        "full_description": "Task 4.1: Enable Dependency Analysis | Duration: 75m | Complexity: 0.6 | Energy: High | Activate dependency analysis tools (Tools 1-10) with ConPort integration",
        "duration_minutes": 75,
        "complexity_score": 0.6,
        "energy_required": "high",
        "cognitive_load": 0.6,
        "component": "Core Module Activation",
        "dependencies": ["2.5", "3.2"],
        "tags": ["phase-1", "activation", "dependency-analysis", "component-4", "critical"]
    },
    {
        "task_id": "4.2",
        "description": "Configure ADHD Engine",
        "full_description": "Task 4.2: Configure ADHD Engine | Duration: 60m | Complexity: 0.5 | Energy: Medium | Integrate Task-Orchestrator ADHD engine with ConPort",
        "duration_minutes": 60,
        "complexity_score": 0.5,
        "energy_required": "medium",
        "cognitive_load": 0.5,
        "component": "Core Module Activation",
        "dependencies": ["4.1"],
        "tags": ["phase-1", "activation", "adhd-engine", "component-4"]
    },
    {
        "task_id": "4.3",
        "description": "Disable Advanced Features",
        "full_description": "Task 4.3: Disable Advanced Features | Duration: 45m | Complexity: 0.4 | Energy: Low | Implement feature flags and disable tools 11-37 (defer to Phase 3)",
        "duration_minutes": 45,
        "complexity_score": 0.4,
        "energy_required": "low",
        "cognitive_load": 0.4,
        "component": "Core Module Activation",
        "dependencies": ["4.1", "4.2"],
        "tags": ["phase-1", "activation", "feature-flags", "component-4"]
    },
    {
        "task_id": "4.4",
        "description": "End-to-End Validation",
        "full_description": "Task 4.4: End-to-End Validation | Duration: 60m | Complexity: 0.6 | Energy: Medium | Validate complete Phase 1 integration works end-to-end",
        "duration_minutes": 60,
        "complexity_score": 0.6,
        "energy_required": "medium",
        "cognitive_load": 0.6,
        "component": "Core Module Activation",
        "dependencies": ["4.1", "4.2", "4.3"],
        "tags": ["phase-1", "activation", "validation", "component-4"]
    },
    # Component 5: Testing (2 hours)
    {
        "task_id": "5.1",
        "description": "Create Integration Test Suite",
        "full_description": "Task 5.1: Create Integration Test Suite | Duration: 60m | Complexity: 0.6 | Energy: High | Comprehensive integration test coverage (>90%)",
        "duration_minutes": 60,
        "complexity_score": 0.6,
        "energy_required": "high",
        "cognitive_load": 0.6,
        "component": "Testing",
        "dependencies": ["4.4"],
        "tags": ["phase-1", "testing", "integration-tests", "component-5"]
    },
    {
        "task_id": "5.2",
        "description": "Performance and Load Testing",
        "full_description": "Task 5.2: Performance and Load Testing | Duration: 60m | Complexity: 0.5 | Energy: Medium | Load testing (>50 events/sec, <500MB memory)",
        "duration_minutes": 60,
        "complexity_score": 0.5,
        "energy_required": "medium",
        "cognitive_load": 0.5,
        "component": "Testing",
        "dependencies": ["5.1"],
        "tags": ["phase-1", "testing", "load-tests", "component-5"]
    }
]

WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"


def main():
    """Import tasks to ConPort."""
    print("🚀 Architecture 3.0 Phase 1 - ConPort Task Import")
    print("=" * 60)
    print(f"📊 Total Tasks: {len(PHASE1_TASKS)}")
    print(f"⏱️  Total Duration: {sum(t['duration_minutes'] for t in PHASE1_TASKS)} minutes (20 hours)")
    print(f"📁 Workspace: {WORKSPACE_ID}")
    print()

    # Display task summary
    print("📋 Task Summary:")
    print()

    current_component = None
    for task in PHASE1_TASKS:
        if task['component'] != current_component:
            current_component = task['component']
            component_tasks = [t for t in PHASE1_TASKS if t['component'] == current_component]
            total_mins = sum(t['duration_minutes'] for t in component_tasks)
            print(f"\n{current_component} ({len(component_tasks)} tasks, {total_mins}m):")

        deps = f" (deps: {', '.join(task['dependencies'])})" if task['dependencies'] else ""
        print(f"  {task['task_id']}: {task['description']} - {task['duration_minutes']}m{deps}")

    print()
    print("=" * 60)
    print()
    print("📝 IMPORT INSTRUCTIONS:")
    print()
    print("Since ConPort MCP tools aren't available in current session,")
    print("you have two options:")
    print()
    print("Option 1: Manual Import via Claude Code")
    print("-" * 60)
    print("When ConPort MCP is available, run:")
    print()
    print("  For each task above, use:")
    print("  mcp__conport__log_progress(")
    print("    workspace_id='/Users/hue/code/dopemux-mvp',")
    print("    status='TODO',")
    print("    description='[full_description from above]',")
    print("    tags=[task tags]")
    print("  )")
    print()
    print("  Then link dependencies with:")
    print("  mcp__conport__link_conport_items(")
    print("    workspace_id='/Users/hue/code/dopemux-mvp',")
    print("    source_item_type='progress_entry',")
    print("    source_item_id=[dependent task ID],")
    print("    target_item_type='progress_entry',")
    print("    target_item_id=[dependency task ID],")
    print("    relationship_type='depends_on'")
    print("  )")
    print()
    print("Option 2: Direct ConPort Database Import")
    print("-" * 60)
    print("If you have direct database access:")
    print()
    print("  psql -h localhost -p 5455 -U dopemux -d dopemux_memory")
    print()
    print("  Then run SQL INSERT statements (generated below)")
    print()

    # Generate SQL for direct import (if needed)
    print("\n" + "=" * 60)
    print("SQL Import Script (if using Option 2):")
    print("=" * 60)
    print()

    for i, task in enumerate(PHASE1_TASKS, 1):
        print(f"-- Task {task['task_id']}: {task['description']}")
        print("INSERT INTO ag_catalog.progress_entries (")
        print("  workspace_id, status, description, tags, custom_metadata")
        print(") VALUES (")
        print(f"  '{WORKSPACE_ID}',")
        print(f"  'TODO',")
        print(f"  '{task['full_description']}',")
        print(f"  ARRAY{task['tags']},")
        print(f"  '{json.dumps({k: v for k, v in task.items() if k not in ['description', 'full_description', 'tags']})}'::jsonb")
        print(");")
        print()

    print("=" * 60)
    print()
    print("✅ Import script complete!")
    print()
    print("💡 Recommended: Use Option 1 (ConPort MCP tools) for automatic linking")


if __name__ == "__main__":
    main()
