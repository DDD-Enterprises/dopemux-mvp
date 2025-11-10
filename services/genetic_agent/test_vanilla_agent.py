#!/usr/bin/env python3
"""Test script for Vanilla Agent with Zen MCP integration."""

import asyncio
import sys
from pathlib import Path

# Add services to path
services_path = Path(__file__).resolve().parent / 'services'
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from genetic_agent.vanilla.vanilla_agent import VanillaAgent
from genetic_agent.core.config import AgentConfig

async def test_vanilla_agent():
    """Test the vanilla agent with Zen MCP integration."""
    try:
        config = AgentConfig()
        agent = VanillaAgent(config)

        print("✅ Vanilla Agent initialized successfully!")
        print(f"Zen URL: {config.zen_url}")
        print(f"Max iterations: {config.max_iterations}")
        print(f"Confidence threshold: {config.confidence_threshold}")

        # Test a simple repair task
        task = {
            'bug_description': 'Simple variable undefined error',
            'file_path': 'test.py',
            'line_number': 5
        }

        print("\n🔧 Testing repair generation...")
        result = await agent.process_task(task)

        print("Repair Result:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"  Iterations: {result.get('iterations', 0)}")
        if result.get('repair'):
            print(f"  Repair code: {result['repair'][:100]}...")
        else:
            print("  No repair generated")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vanilla_agent())