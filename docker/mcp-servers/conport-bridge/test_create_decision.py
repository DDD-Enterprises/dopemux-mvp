#!/usr/bin/env python3
"""
Test script to create a decision in ConPort MCP database
This simulates what happens when Claude Code creates a decision
"""

import sqlite3
from datetime import datetime
import json

db_path = "/Users/hue/code/dopemux-mvp/context_portal/context.db"

# Create a test decision
decision = {
    "summary": "Test Event Bridge integration",
    "rationale": "Validating that ConPort MCP → Redis Streams → Agents pipeline works",
    "implementation_details": json.dumps({
        "approach": "Watch SQLite file changes",
        "publish_to": "Redis Streams",
        "consumers": ["Serena", "Task-Orchestrator"]
    }),
    "tags": json.dumps(["event-bridge", "integration", "test"]),
    "timestamp": datetime.utcnow().isoformat()
}

# Insert into database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO decisions (summary, rationale, implementation_details, tags, timestamp)
    VALUES (?, ?, ?, ?, ?)
""", (
    decision["summary"],
    decision["rationale"],
    decision["implementation_details"],
    decision["tags"],
    decision["timestamp"]
))

decision_id = cursor.lastrowid
conn.commit()
conn.close()

print(f"✅ Created decision #{decision_id}")
print(f"   Summary: {decision['summary']}")
print(f"   Rationale: {decision['rationale']}")
print(f"\n⏳ Event should be published to Redis within 1-2 seconds...")
