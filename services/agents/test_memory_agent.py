"""
Test script for MemoryAgent with ConPort integration.

Run from project root: python services/agents/test_memory_agent.py
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from memory_agent import MemoryAgent, SessionState


async def test_basic_functionality():
    """Test MemoryAgent basic functionality."""

    print("\n" + "="*60)
    print("MemoryAgent Functionality Test")
    print("="*60 + "\n")

    # Initialize agent
    agent = MemoryAgent(
        workspace_id="/Users/hue/code/dopemux-mvp",
        auto_save_interval=30
    )

    print("✅ MemoryAgent initialized\n")

    # Start session
    await agent.start_session(
        task_description="Implement JWT authentication with refresh tokens",
        mode="code",
        complexity=0.6,
        energy_level="high"
    )

    print("✅ Session started\n")

    # Simulate work for 35 seconds (triggers auto-save at 30s)
    print("⏱️  Working for 35 seconds (auto-save at 30s)...\n")
    await asyncio.sleep(35)

    # Update session state
    await agent.update_state(
        current_focus="Creating JWT token generation function",
        open_files=["src/auth/jwt.py", "src/auth/models.py"],
        cursor_positions={"src/auth/jwt.py": 45},
        next_steps=[
            "Add token validation",
            "Implement refresh token rotation",
            "Write tests"
        ],
        attention_state="focused"
    )

    print("✅ Session state updated\n")

    # Log a decision
    await agent.log_decision(
        "Use RS256 algorithm for JWT signing (more secure than HS256)"
    )

    print("✅ Decision logged\n")

    # Continue work for another 35 seconds
    print("⏱️  Continuing for 35 more seconds (another auto-save)...\n")
    await asyncio.sleep(35)

    # End session
    summary = await agent.end_session(outcome="completed")

    print("\n" + "="*60)
    print("Session Summary:")
    print("="*60)
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Show metrics
    print("\n" + "="*60)
    print("MemoryAgent Metrics:")
    print("="*60)
    metrics = agent.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
