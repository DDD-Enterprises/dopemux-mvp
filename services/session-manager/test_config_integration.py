#!/usr/bin/env python3
"""
Test Configuration Integration
Demonstrates using the new config system with existing agent spawner
"""

import sys
from src.agent_spawner import AgentSpawner
from src.agent_config_factory import auto_configure_spawner, create_agent_configs_from_file


def test_config_integration():
    """Test the new configuration system integration."""
    print("🧪 Testing Configuration Integration")
    print("=" * 60)

    # Method 1: Auto-configure spawner (easiest)
    print("\n📋 Method 1: Auto-configure spawner")
    print("-" * 60)
    spawner1 = AgentSpawner()
    auto_configure_spawner(spawner1)

    # Method 2: Manual registration (more control)
    print("\n📋 Method 2: Manual registration from config")
    print("-" * 60)
    spawner2 = AgentSpawner()
    configs = create_agent_configs_from_file()

    for agent_type, config in configs.items():
        print(f"✅ Registering {agent_type.value}...")
        spawner2.register_agent(agent_type, config)

    print(f"\n✅ Registered {len(configs)} agents")

    # Show what we got
    print("\n📊 Configured Agents:")
    print("-" * 60)
    for agent_type, agent in spawner2.agents.items():
        print(f"\n  {agent_type.value}:")
        print(f"    Command: {agent.config.command}")
        print(f"    Auto-restart: {agent.config.auto_restart}")
        print(f"    Status: {agent.status.value}")

    print("\n✅ Configuration integration test passed!")
    print("\n💡 Next: Run spawner.start_all() to start agents")

    return True


if __name__ == "__main__":
    try:
        success = test_config_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
