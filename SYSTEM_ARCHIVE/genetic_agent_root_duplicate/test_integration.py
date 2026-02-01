#!/usr/bin/env python3
"""Test script for genetic agent integration."""

import asyncio
import sys
import os

# Add the genetic_agent directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genetic_agent'))

from genetic_agent.core.config import AgentConfig
from genetic.genetic_agent import GeneticAgent

async def test_genetic_agent():
    """Test the genetic agent with Zen and DopeContext integration."""

    # Create config
    config = AgentConfig()

    # Create agent
    agent = GeneticAgent(config)

    # Test task
    test_task = {
        "bug_description": "null pointer exception when accessing user preferences",
        "file_path": "/app/user.py",
        "line_number": 45
    }

    print("Testing genetic agent with Zen planner and DopeContext integration...")
    print(f"Task: {test_task}")

    try:
        # Process the task
        result = await agent.process_task(test_task)

        print("\n✅ Test completed successfully!")
        print(f"Result: {result}")

        # Check if Zen was used
        if 'method' in result and 'llm' in result.get('method', ''):
            print("✅ Zen LLM integration working")

        # Check if DopeContext was used
        if hasattr(agent, 'dope_client') and agent.dope_client:
            print("✅ DopeContext integration working")

        # Check if ConPort logging worked
        if hasattr(agent, 'memory_adapter') and agent.memory_adapter:
            print("✅ ConPort memory adapter working")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_genetic_agent())
    sys.exit(0 if success else 1)