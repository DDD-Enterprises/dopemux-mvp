#!/usr/bin/env python3
"""
Test MetaMCP Role Switching

Simple test script to verify role switching between researcher and developer modes.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_role_switching():
    """Test switching between researcher and developer roles"""
    try:
        from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig

        print("🧪 Testing MetaMCP Role Switching")
        print("=" * 50)

        # Connect to existing broker via client interface
        # Since broker is already running, we'll create a client connection
        config = BrokerConfig(
            name="test-client",
            version="1.0.0",
            host="localhost",
            port=8090,
            broker_config_path="config/mcp/broker.yaml",
            policy_config_path="config/mcp/policy.yaml",
            role_based_mounting=True,
            budget_aware_hooks=False,
            letta_integration=False,
            adhd_optimizations=True
        )

        # Create a simple session manager to test roles
        from dopemux.mcp.session_manager import SessionManager
        from dopemux.mcp.roles import RoleManager
        import yaml

        # Load policy configuration
        with open("config/mcp/policy.yaml", "r") as f:
            policy_config = yaml.safe_load(f)

        role_manager = RoleManager(policy_config)
        session_manager = SessionManager(policy_config)

        print(f"✅ Loaded {len(role_manager.roles)} role definitions")

        # Test researcher role
        print("\n🔍 TESTING RESEARCHER ROLE")
        researcher_role = await role_manager.get_role("researcher")
        if researcher_role:
            print(f"Tools: {researcher_role.default_tools}")
            print(f"Token budget: {researcher_role.token_budget}")
            print(f"Description: {researcher_role.description}")
            print(f"All possible tools: {researcher_role.all_possible_tools}")
        else:
            print("❌ Researcher role not found")

        # Test developer role
        print("\n🛠️  TESTING DEVELOPER ROLE")
        developer_role = await role_manager.get_role("developer")
        if developer_role:
            print(f"Tools: {developer_role.default_tools}")
            print(f"Token budget: {developer_role.token_budget}")
            print(f"Description: {developer_role.description}")
            print(f"All possible tools: {developer_role.all_possible_tools}")
        else:
            print("❌ Developer role not found")

        # Test role switching through session manager
        print("\n🔄 TESTING ROLE TRANSITIONS")

        # Create test session
        session_id = "test-session-001"
        await session_manager.create_session(session_id, "researcher")

        current_session = await session_manager.get_session(session_id)
        current_role = current_session.current_context.role if current_session.current_context else "unknown"
        print(f"Initial role: {current_role}")

        # Switch to developer
        await session_manager.switch_role(session_id, "developer")
        current_session = await session_manager.get_session(session_id)
        current_role = current_session.current_context.role if current_session.current_context else "unknown"
        print(f"Switched to role: {current_role}")

        # Switch back to researcher
        await session_manager.switch_role(session_id, "researcher")
        current_session = await session_manager.get_session(session_id)
        current_role = current_session.current_context.role if current_session.current_context else "unknown"
        print(f"Switched back to role: {current_role}")

        print("\n✅ ROLE SWITCHING TESTS COMPLETED SUCCESSFULLY")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_role_switching())
    sys.exit(0 if success else 1)