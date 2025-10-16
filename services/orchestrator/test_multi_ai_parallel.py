#!/usr/bin/env python3
"""
Test Multiple AI CLIs in Parallel with PTY + Tmux Integration
The REAL multi-AI orchestration test!

This tests:
1. Spawning Claude, Gemini, Codex with PTY
2. Assigning each to a tmux pane
3. Sending commands in parallel
4. Capturing responses from all AIs
"""

import time
from src.tmux_manager import TmuxLayoutManager
from src.agent_spawner_pty import PTYAgent, AgentConfig, AgentType, AgentStatus


def test_multi_ai_in_tmux():
    """The full integration test."""

    print("🚀 Multi-AI Parallel Orchestration Test")
    print("=" * 60)

    # Step 1: Create tmux session with 4 panes
    print("\n1. Creating tmux session (high energy = 4 panes)...")
    tmux = TmuxLayoutManager(session_name="dopemux-multi-ai-test")
    session = tmux.create_session(energy_level="high")

    print(f"   ✅ Tmux session: {session.name}")
    print(f"   📊 Panes: {len(tmux.panes)}")
    for name, pane in tmux.panes.items():
        print(f"      - {name}: {pane.id}")

    # Step 2: Create AI agents with PTY
    print("\n2. Creating AI agents...")

    claude_agent = PTYAgent(
        AgentConfig(
            agent_type=AgentType.CLAUDE,
            command=["/Users/hue/.local/bin/claude", "chat"],
            env={},
        )
    )

    gemini_agent = PTYAgent(
        AgentConfig(
            agent_type=AgentType.GEMINI,
            command=["gemini"],
            env={},
        )
    )

    codex_agent = PTYAgent(
        AgentConfig(
            agent_type=AgentType.CODEX,
            command=["/Users/hue/.nvm/versions/node/v22.18.0/bin/codex", "chat"],
            env={},
        )
    )

    # Step 3: Start all agents
    print("\n3. Starting all AI agents...")

    agents = {
        "Claude": claude_agent,
        "Gemini": gemini_agent,
        "Codex": codex_agent,
    }

    results = {}
    for name, agent in agents.items():
        success = agent.start()
        results[name] = success
        time.sleep(0.5)  # Brief delay between spawns

    # Step 4: Show status
    print("\n4. Agent Status:")
    for name, agent in agents.items():
        icon = "✅" if results[name] else "❌"
        status = agent.status.value
        pid = f"PID: {agent.pid}" if agent.pid else "No PID"
        print(f"   {icon} {name}: {status} ({pid})")

    # Step 5: Wait for initialization
    print("\n5. Waiting for agents to initialize (5 seconds)...")
    time.sleep(5)

    # Step 6: Health check
    print("\n6. Health Check:")
    for name, agent in agents.items():
        healthy = agent.is_healthy()
        icon = "💚" if healthy else "💔"
        print(f"   {icon} {name}: {'Healthy' if healthy else 'Not healthy'}")

    # Step 7: Send parallel commands
    print("\n7. Sending test question to all healthy agents in parallel...")

    test_question = "What is 2 + 2?"

    for name, agent in agents.items():
        if agent.is_healthy():
            print(f"   📤 Sending to {name}...")
            agent.send_command(test_question)

    # Step 8: Wait for responses
    print("\n8. Waiting for responses (5 seconds)...")
    time.sleep(5)

    # Step 9: Collect responses
    print("\n9. Responses:")

    for name, agent in agents.items():
        output = agent.get_output(clear=False)
        print(f"\n   {name} ({len(output)} lines):")
        if output:
            # Show last 10 lines (likely the response)
            for line in output[-10:]:
                if line.strip():
                    print(f"      {line[:80]}")

    # Step 10: Cleanup
    print("\n\n10. Cleanup:")
    for name, agent in agents.items():
        if agent.status == AgentStatus.RUNNING:
            agent.stop()

    print("\n✅ Multi-AI parallel test complete!")

    # Summary
    healthy_count = sum(1 for agent in agents.values() if agent.is_healthy())
    print(f"\n📊 Final: {healthy_count}/3 agents healthy and responsive")

    print(f"\n💡 To see the tmux session:")
    print(f"   tmux attach -t {session.name}")

    return healthy_count


if __name__ == "__main__":
    try:
        healthy = test_multi_ai_in_tmux()
        print(f"\n{'🎉 SUCCESS!' if healthy >= 2 else '⚠️ PARTIAL SUCCESS'}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
