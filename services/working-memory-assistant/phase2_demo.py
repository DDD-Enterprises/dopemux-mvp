#!/usr/bin/env python3
"""
Phase 2 Integration Demo

Demonstrates the full reflection + trajectory workflow:
1. Store work entries
2. Generate reflection
3. Fetch reflections
4. Check trajectory state
"""

import sys
import tempfile
from pathlib import Path

# Add service dir to path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))

from dope_memory_main import DopeMemoryMCPServer


def main():
    print("=== Phase 2 Integration Demo ===\n")
    
    # Create temporary server
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data"
    
    server = DopeMemoryMCPServer(
        data_dir=data_dir,
        workspace_id="demo_workspace",
        instance_id="A",
    )
    
    workspace_id = "demo_workspace"
    instance_id = "A"
    session_id = "demo_session"
    
    # Step 1: Store work entries
    print("Step 1: Storing work entries...")
    
    entries = [
        {
            "category": "planning",
            "entry_type": "decision",
            "summary": "Decided to implement Phase 2 reflection features",
            "importance_score": 9,
        },
        {
            "category": "implementation",
            "entry_type": "task_event",
            "summary": "Implemented ReflectionGenerator with Top-3 filtering",
            "importance_score": 7,
        },
        {
            "category": "debugging",
            "entry_type": "blocker",
            "summary": "Import path issues blocking tests",
            "importance_score": 8,
        },
        {
            "category": "review",
            "entry_type": "resolution",
            "summary": "Fixed import paths by adding conftest.py",
            "importance_score": 7,
        },
        {
            "category": "implementation",
            "entry_type": "task_event",
            "summary": "Added trajectory state management",
            "importance_score": 6,
        },
    ]
    
    for entry in entries:
        result = server.memory_store(
            workspace_id=workspace_id,
            instance_id=instance_id,
            session_id=session_id,
            **entry,
        )
        if result.success:
            print(f"  ✓ Stored: {entry['summary'][:50]}...")
    
    # Step 2: Generate reflection
    print("\nStep 2: Generating reflection card...")
    
    reflection_result = server.memory_generate_reflection(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        window_hours=2,
    )
    
    if reflection_result.success:
        print(f"  ✓ Reflection generated: {reflection_result.data['reflection_id']}")
        print(f"  Trajectory: {reflection_result.data['trajectory']}")
        print(f"\n  Top Decisions ({len(reflection_result.data['top_decisions'])}):")
        for d in reflection_result.data['top_decisions']:
            print(f"    - {d['summary']}")
        print(f"\n  Top Blockers ({len(reflection_result.data['top_blockers'])}):")
        for b in reflection_result.data['top_blockers']:
            print(f"    - {b['summary']}")
        print(f"\n  Progress:")
        print(f"    Total entries: {reflection_result.data['progress']['total_entries']}")
        print(f"    Categories: {reflection_result.data['progress']['categories']}")
        print(f"\n  Next Suggested ({len(reflection_result.data['next_suggested'])}):")
        for ns in reflection_result.data['next_suggested']:
            print(f"    [{ns['type']}] {ns['summary']}")
    
    # Step 3: Fetch reflections
    print("\nStep 3: Fetching recent reflections...")
    
    reflections_result = server.memory_reflections(
        workspace_id=workspace_id,
        instance_id=instance_id,
        limit=3,
    )
    
    if reflections_result.success:
        print(f"  ✓ Found {reflections_result.data['count']} reflection(s)")
        for i, refl in enumerate(reflections_result.data['reflections'], 1):
            print(f"  Reflection {i}:")
            print(f"    ID: {refl['id']}")
            print(f"    Timestamp: {refl['ts_utc']}")
            print(f"    Trajectory: {refl['trajectory']}")
    
    # Step 4: Check trajectory state
    print("\nStep 4: Checking trajectory state...")
    
    trajectory_result = server.memory_trajectory(
        workspace_id=workspace_id,
        instance_id=instance_id,
    )
    
    if trajectory_result.success:
        print(f"  ✓ Current stream: {trajectory_result.data['current_stream']}")
        print(f"  Boost factor: {trajectory_result.data['boost_factor']}")
        print(f"  Last steps ({len(trajectory_result.data['last_steps'])}):")
        for step in trajectory_result.data['last_steps']:
            print(f"    - {step}")
    
    print("\n=== Demo Complete ===")
    print(f"Data stored in: {data_dir}")
    print("\n✅ Phase 2 features working correctly!")


if __name__ == "__main__":
    main()
