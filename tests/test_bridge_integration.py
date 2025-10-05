#!/usr/bin/env python3
"""
Test the updated Leantime JSON-RPC bridge integration
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.dopemux.config.manager import ConfigManager
from src.integrations.leantime_bridge import create_leantime_bridge

async def test_bridge():
    """Test the Leantime bridge with proper configuration"""

    # Create a simple config adapter for the bridge
    class SimpleConfig:
        def __init__(self, data):
            self.data = data

        def get(self, key, default=None):
            return self.data.get(key, default)

    # Create config with the correct API token
    config = SimpleConfig({
        'leantime.api_url': 'http://localhost:8080',
        'leantime.api_token': 'lt_OOeOe2noZt3PFF2eG3G0RQQlifN9FDzg_N86U5j5GGV7i7u3VD2XNvksGAEzNYA4B'
    })

    print("🔗 Testing Leantime JSON-RPC Bridge Integration")
    print("=" * 50)

    async with create_leantime_bridge(config) as bridge:
        print("✅ Bridge created and connected successfully")

        # Test project retrieval
        print("\n📋 Testing project retrieval...")
        projects = await bridge.get_projects(limit=5)
        print(f"✅ Retrieved {len(projects)} projects")

        for project in projects:
            print(f"   - Project: {project.name} (ID: {project.id})")

        # Test task retrieval if we have projects
        if projects:
            print(f"\n📝 Testing task retrieval for project {projects[0].id}...")
            try:
                tasks = await bridge.get_tasks(project_id=projects[0].id, limit=5)
                print(f"✅ Retrieved {len(tasks)} tasks")

                for task in tasks:
                    print(f"   - Task: {task.headline} (Load: {task.cognitive_load})")
            except Exception as e:
                print(f"⚠️  Task retrieval not yet working: {e}")

        # Test ADHD features
        print("\n🧠 Testing ADHD optimizations...")
        if projects:
            adhd_tasks = await bridge.get_adhd_optimized_tasks(
                user_id=1,
                attention_state="focused"
            )
            print(f"✅ ADHD-optimized tasks: {len(adhd_tasks)}")

        # Test health check
        print("\n🔍 Testing health check...")
        health = await bridge.health_check()
        print(f"✅ Health status: {health['status']}")
        print(f"✅ Connected: {health['connected']}")
        print(f"✅ API responsive: {health['api_responsive']}")

if __name__ == "__main__":
    asyncio.run(test_bridge())