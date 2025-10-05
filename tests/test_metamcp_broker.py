#!/usr/bin/env python3
"""
Test script for MetaMCP Broker initialization and basic functionality.

This script tests the core MetaMCP broker components to ensure they work
together properly before integration into the larger Dopemux system.
"""

import asyncio
import sys
import logging
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig
from dopemux.mcp.roles import RoleManager
from dopemux.mcp.token_manager import TokenBudgetManager
from dopemux.mcp.session_manager import SessionManager
from dopemux.mcp.hooks import PreToolHookManager
from dopemux.mcp.server_manager import MCPServerManager
from dopemux.mcp.observability import MetricsCollector, HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_component_initialization():
    """Test individual component initialization."""
    logger.info("Testing individual component initialization...")

    try:
        # Test policy loading
        policy_config_path = "config/mcp/policy.yaml"
        if not os.path.exists(policy_config_path):
            logger.error(f"Policy config not found: {policy_config_path}")
            return False

        with open(policy_config_path, 'r') as f:
            import yaml
            policy_config = yaml.safe_load(f)

        logger.info("✅ Policy configuration loaded successfully")

        # Test role manager
        role_manager = RoleManager(policy_config)
        roles = await role_manager.list_roles()
        logger.info(f"✅ RoleManager initialized with {len(roles)} roles")

        # Test token manager
        token_manager = TokenBudgetManager(policy_config, db_path="/tmp/test_metamcp_tokens.db")
        session_budget = await token_manager.initialize_session_budget("test-session", "developer")
        logger.info(f"✅ TokenBudgetManager initialized, test budget: {session_budget.total_budget} tokens")

        # Test session manager (simulated)
        session_manager = SessionManager(policy_config)
        logger.info("✅ SessionManager initialized")

        # Test hooks manager
        hooks_manager = PreToolHookManager(policy_config, token_manager)
        logger.info("✅ PreToolHookManager initialized")

        # Test observability
        metrics = MetricsCollector()
        health_monitor = HealthMonitor()
        metrics.record_startup()
        logger.info("✅ Observability components initialized")

        return True

    except Exception as e:
        logger.error(f"❌ Component initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_broker_initialization():
    """Test MetaMCP Broker initialization."""
    logger.info("Testing MetaMCP Broker initialization...")

    try:
        # Check required config files
        broker_config_path = "config/mcp/broker.yaml"
        policy_config_path = "config/mcp/policy.yaml"

        if not os.path.exists(broker_config_path):
            logger.error(f"Broker config not found: {broker_config_path}")
            return False

        if not os.path.exists(policy_config_path):
            logger.error(f"Policy config not found: {policy_config_path}")
            return False

        # Create broker config
        config = BrokerConfig(
            broker_config_path=broker_config_path,
            policy_config_path=policy_config_path,
            # Disable actual server connections for testing
            role_based_mounting=True,
            budget_aware_hooks=True,
            letta_integration=False,  # Disable for testing
            adhd_optimizations=True
        )

        logger.info("✅ Broker configuration created")

        # Initialize broker (but don't start servers)
        broker = MetaMCPBroker(config)
        logger.info("✅ MetaMCP Broker instance created")

        # Test broker methods without starting servers
        health_status = await broker.get_broker_health()
        logger.info(f"✅ Broker health check: {health_status.get('overall_status', 'unknown')}")

        # Test session creation
        session_status = await broker.get_session_status("test-session-123")
        logger.info(f"✅ Session status check: exists={session_status.get('exists', False)}")

        # Test role switch (creates session)
        try:
            role_switch_result = await broker.switch_role("test-session-123", "developer")
            logger.info(f"✅ Role switch test: success={role_switch_result.get('success', False)}")
        except Exception as e:
            logger.warning(f"⚠️  Role switch test failed (expected without server manager): {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Broker initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_role_system():
    """Test role management functionality."""
    logger.info("Testing role management system...")

    try:
        # Load policy config
        with open("config/mcp/policy.yaml", 'r') as f:
            import yaml
            policy_config = yaml.safe_load(f)

        role_manager = RoleManager(policy_config)

        # Test role listing
        roles = await role_manager.list_roles()
        logger.info(f"✅ Found {len(roles)} roles: {[r.name for r in roles]}")

        # Test role details
        for role in roles[:3]:  # Test first 3 roles
            role_summary = role_manager.get_role_summary(role.name)
            logger.info(f"✅ Role '{role.name}': {len(role_summary['default_tools'])} tools, {role_summary['token_budget']} tokens")

        # Test role suggestions
        context = {
            'task_description': 'implement a new authentication feature',
            'file_patterns': ['.py', '.js'],
            'time_of_day': 10
        }

        suggested_role = await role_manager.suggest_role_for_context(context)
        logger.info(f"✅ Role suggestion for context: {suggested_role}")

        # Test role transitions
        valid_transition = await role_manager.validate_role_transition("developer", "reviewer")
        logger.info(f"✅ Role transition validation (developer->reviewer): {valid_transition}")

        return True

    except Exception as e:
        logger.error(f"❌ Role system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_token_management():
    """Test token budget management."""
    logger.info("Testing token budget management...")

    try:
        # Load policy config
        with open("config/mcp/policy.yaml", 'r') as f:
            import yaml
            policy_config = yaml.safe_load(f)

        token_manager = TokenBudgetManager(policy_config, db_path="/tmp/test_metamcp_tokens.db")

        # Test budget initialization
        budget = await token_manager.initialize_session_budget("test-session", "developer")
        logger.info(f"✅ Initialized budget: {budget.total_budget} tokens for developer role")

        # Test token usage recording
        updated_budget = await token_manager.record_usage(
            "test-session",
            tokens_used=1500,
            tool_name="claude-context",
            method="search"
        )
        logger.info(f"✅ Recorded usage: {updated_budget.used_tokens}/{updated_budget.total_budget} tokens used")

        # Test budget availability check
        available, message = await token_manager.check_budget_availability("test-session", 5000)
        logger.info(f"✅ Budget availability check: {available} - {message}")

        # Test optimization suggestions
        suggestions = await token_manager.get_optimization_suggestions("test-session")
        logger.info(f"✅ Got {len(suggestions)} optimization suggestions")

        # Test analytics
        analytics = await token_manager.get_usage_analytics(session_id="test-session")
        logger.info(f"✅ Usage analytics: {analytics.get('total_stats', {})}")

        return True

    except Exception as e:
        logger.error(f"❌ Token management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hooks_system():
    """Test pre-tool hooks optimization."""
    logger.info("Testing pre-tool hooks system...")

    try:
        # Load policy config
        with open("config/mcp/policy.yaml", 'r') as f:
            import yaml
            policy_config = yaml.safe_load(f)

        # Initialize token manager for hooks
        token_manager = TokenBudgetManager(policy_config, db_path="/tmp/test_metamcp_tokens.db")
        await token_manager.initialize_session_budget("test-session", "developer")

        hooks_manager = PreToolHookManager(policy_config, token_manager)

        # Test claude-context optimization
        original_call = {
            'tool': 'claude-context',
            'method': 'search',
            'args': {
                'query': 'authentication implementation',
                'maxResults': 20,  # Should be trimmed
                'includeTests': True
            }
        }

        session_context = {
            'session_id': 'test-session',
            'role': 'developer'
        }

        optimized_call, optimizations = await hooks_manager.pre_tool_check(original_call, session_context)
        logger.info(f"✅ Applied {len(optimizations)} optimizations to claude-context call")

        for opt in optimizations:
            logger.info(f"   - {opt.action_taken.value}: saved ~{opt.estimated_token_savings} tokens")

        # Test sequential-thinking optimization
        thinking_call = {
            'tool': 'sequential-thinking',
            'method': 'analyze',
            'args': {
                'query': 'complex system architecture',
                'maxDepth': 15  # Should be trimmed
            }
        }

        optimized_thinking, thinking_optimizations = await hooks_manager.pre_tool_check(thinking_call, session_context)
        logger.info(f"✅ Applied {len(thinking_optimizations)} optimizations to sequential-thinking call")

        # Test optimization stats
        stats = hooks_manager.get_optimization_stats()
        logger.info(f"✅ Optimization stats: {stats}")

        return True

    except Exception as e:
        logger.error(f"❌ Hooks system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all MetaMCP tests."""
    logger.info("🚀 Starting MetaMCP Broker Tests")
    logger.info("=" * 60)

    test_results = []

    # Test individual components
    logger.info("\n📋 Testing Component Initialization...")
    test_results.append(("Component Initialization", await test_component_initialization()))

    # Test role system
    logger.info("\n👤 Testing Role Management System...")
    test_results.append(("Role Management", await test_role_system()))

    # Test token management
    logger.info("\n💰 Testing Token Budget Management...")
    test_results.append(("Token Management", await test_token_management()))

    # Test hooks system
    logger.info("\n🪝 Testing Pre-tool Hooks System...")
    test_results.append(("Hooks System", await test_hooks_system()))

    # Test broker initialization
    logger.info("\n🤖 Testing MetaMCP Broker...")
    test_results.append(("Broker Initialization", await test_broker_initialization()))

    # Print results summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status:<8} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    logger.info("-" * 60)
    logger.info(f"Total: {passed + failed} tests | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        logger.info("🎉 All tests passed! MetaMCP system is ready for integration.")
        return True
    else:
        logger.error(f"💥 {failed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    # Ensure we're in the right directory
    if not os.path.exists("config/mcp/policy.yaml"):
        logger.error("Please run this script from the dopemux-mvp root directory")
        sys.exit(1)

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)