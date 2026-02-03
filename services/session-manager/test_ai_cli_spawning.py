#!/usr/bin/env python3
"""
Test AI CLI Spawning - Integration Test
Verify we can spawn and communicate with Claude, Gemini, and Codex
"""

import sys
import time
from src.agent_spawner import AgentSpawner, AgentConfig, AgentType


def test_spawn_all_ais():
    """Test spawning all 3 AI CLI instances."""

    print("🚀 Testing AI CLI Spawning")
    print("=" * 60)

    spawner = AgentSpawner()

    # Configure Claude
    print("\n1. Configuring Claude Code...")
    spawner.register_agent(
        AgentType.CLAUDE,
        AgentConfig(
            agent_type=AgentType.CLAUDE,
            command=["/Users/hue/.local/bin/claude", "chat"],
            env={},
            auto_restart=True,
        ),
    )

    # Configure Gemini
    print("2. Configuring Gemini CLI...")
    spawner.register_agent(
        AgentType.GEMINI,
        AgentConfig(
            agent_type=AgentType.GEMINI,
            command=["gemini", "--output-format", "json"],
            env={},
            auto_restart=True,
        ),
    )

    # Configure Codex (using available codex CLI)
    print("3. Configuring Codex CLI...")
    spawner.register_agent(
        AgentType.CODEX,
        AgentConfig(
            agent_type=AgentType.CODEX,
            command=["/Users/hue/.nvm/versions/node/v22.18.0/bin/codex", "chat"],
            env={},
            auto_restart=True,
        ),
    )

    # Start all agents
    print("\n🎬 Starting all agents...")
    results = spawner.start_all()

    print("\n📊 Startup Results:")
    for agent_type, success in results.items():
        icon = "✅" if success else "❌"
        print(f"  {icon} {agent_type.value}: {'Running' if success else 'Failed'}")

    # Wait a bit for agents to initialize
    print("\n⏳ Waiting for agents to initialize...")
    time.sleep(3)

    # Check health
    print("\n💓 Health Check:")
    for agent_type, agent in spawner.agents.items():
        healthy = agent.is_healthy()
        icon = "✅" if healthy else "❌"
        status = agent.status.value
        print(f"  {icon} {agent_type.value}: {status}")

    # Show full status
    print("\n📈 Detailed Status:")
    import json
    status = spawner.get_status()
    print(json.dumps(status, indent=2))

    # Test sending command to each agent (if healthy)
    print("\n🧪 Testing Command Send:")

    for agent_type in [AgentType.CLAUDE, AgentType.GEMINI, AgentType.CODEX]:
        agent = spawner.agents.get(agent_type)
        if agent and agent.is_healthy():
            print(f"\n  Testing {agent_type.value}...")
            try:
                response = spawner.send_to_agent(agent_type, "What is 2+2?")
                if response:
                    print(f"    ✅ Got response ({len(response)} lines)")
                    if response:
                        print(f"    First line: {response[0][:60]}...")
                else:
                    print(f"    ⚠️ No response received")
            except Exception as e:
                print(f"    ❌ Error: {e}")

    # Cleanup
    print("\n\n🧹 Cleaning up...")
    spawner.stop_all()

    print("\n✅ AI CLI spawning test complete!")

    # Summary
    success_count = sum(1 for success in results.values() if success)
    print(f"\n📊 Summary: {success_count}/3 AI CLIs started successfully")

    return success_count == 3


if __name__ == "__main__":
    try:
        success = test_spawn_all_ais()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
