#!/usr/bin/env python3
"""
Phase 2 Integration Demo.

Minimal runtime demo aligned with current MCP surface:
1. Store entries
2. Search entries
3. Print IDs + summaries
"""

import sys
import tempfile
import os
from pathlib import Path

# Add service dir to path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir))

from dope_memory_main import DopeMemoryMCPServer


def main():
    print("=== Phase 2 Integration Demo ===\n")

    # Create temporary isolated ledger
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir)
    ledger_path = data_dir / "chronicle.sqlite"
    os.environ["DOPEMUX_CAPTURE_LEDGER_PATH"] = str(ledger_path)

    server = DopeMemoryMCPServer(
        workspace_id="demo_workspace",
        instance_id="A",
    )

    workspace_id = "demo_workspace"
    instance_id = "A"

    print("Step 1: Storing demo entries...")
    entries = [
        {
            "category": "planning",
            "entry_type": "decision",
            "summary": "Demo: decide rollout sequence",
            "importance_score": 9,
        },
        {
            "category": "debugging",
            "entry_type": "blocker",
            "summary": "Demo: blocker in adapter wiring",
            "importance_score": 7,
        },
        {
            "category": "implementation",
            "entry_type": "milestone",
            "summary": "Demo: shipped deterministic pagination",
            "importance_score": 6,
        },
    ]

    for entry in entries:
        result = server.memory_store(
            workspace_id=workspace_id,
            instance_id=instance_id,
            **entry,
        )
        if result.success:
            print(f"  ✓ Stored: {entry['summary'][:50]}...")
        else:
            raise RuntimeError(f"Store failed: {result.error}")

    print("\nStep 2: Searching demo entries...")
    search_result = server.memory_search(
        query="Demo:",
        workspace_id=workspace_id,
        instance_id=instance_id,
        top_k=3,
    )
    if not search_result.success:
        raise RuntimeError(f"Search failed: {search_result.error}")

    items = search_result.data.get("items", [])
    print(f"  ✓ Found {len(items)} item(s)")
    for item in items:
        print(f"    - {item['id']} | {item['summary']}")

    print("\n=== Demo Complete ===")
    print(f"Data stored in: {ledger_path}")
    print("\n✅ Store/Search demo working correctly!")


if __name__ == "__main__":
    main()
