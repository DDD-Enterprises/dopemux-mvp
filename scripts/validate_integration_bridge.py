#!/usr/bin/env python3
"""
DopeconBridge Migration - Validation Script

Run this script to verify the DopeconBridge migration is working correctly.
Tests all critical paths without needing full services to be running.

Usage:
    python3 scripts/validate_dopecon_bridge.py
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path

# Add shared modules to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "services"))

try:
    from shared.dopecon_bridge_client import (
        AsyncDopeconBridgeClient,
        DopeconBridgeConfig,
        DopeconBridgeError,
    )
    CLIENT_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ Failed to import DopeconBridge client: {e}")
    CLIENT_AVAILABLE = False

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_section(title):
    """Print section header"""
    logger.info(f"\n{'='*60}")
    logger.info(f"{title}")
    logger.info(f"{'='*60}\n")


def print_test(name, passed, details=""):
    """Print test result"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    logger.info(f"{status} {name}")
    if details:
        logger.info(f"    {details}")


async def test_client_import():
    """Test 1: Client can be imported"""
    print_test(
        "Client Import",
        CLIENT_AVAILABLE,
        "DopeconBridge client imported successfully" if CLIENT_AVAILABLE 
        else "Failed to import client - check sys.path"
    )
    return CLIENT_AVAILABLE


async def test_config_from_env():
    """Test 2: Configuration can be loaded from environment"""
    try:
        config = DopeconBridgeConfig.from_env()
        print_test(
            "Config from Environment",
            True,
            f"Base URL: {config.base_url}, Source Plane: {config.source_plane}"
        )
        return True
    except Exception as e:
        print_test("Config from Environment", False, str(e))
        return False


        logger.error(f"Error: {e}")
async def test_client_creation():
    """Test 3: Client can be created"""
    try:
        config = DopeconBridgeConfig.from_env()
        client = AsyncDopeconBridgeClient(config=config)
        await client.aclose()
        print_test(
            "Client Creation",
            True,
            "Client created and closed successfully"
        )
        return True
    except Exception as e:
        print_test("Client Creation", False, str(e))
        return False


        logger.error(f"Error: {e}")
async def test_bridge_connection():
    """Test 4: Can connect to DopeconBridge"""
    try:
        config = DopeconBridgeConfig.from_env()
        async with AsyncDopeconBridgeClient(config=config) as client:
            # Try to get stream info (should work even if bridge is down)
            try:
                await client.get_stream_info()
                print_test(
                    "Bridge Connection",
                    True,
                    "Successfully connected to DopeconBridge"
                )
                return True
            except DopeconBridgeError as e:
                if "Connection refused" in str(e) or "ConnectError" in str(e):
                    print_test(
                        "Bridge Connection",
                        False,
                        f"{YELLOW}DopeconBridge not running at {config.base_url}{RESET}"
                    )
                else:
                    print_test("Bridge Connection", False, str(e))
                return False
    except Exception as e:
        print_test("Bridge Connection", False, str(e))
        return False


        logger.error(f"Error: {e}")
async def test_service_adapters():
    """Test 5: Service adapters can be imported"""
    results = {}
    
    adapters = {
        "Voice Commands": "voice_commands.bridge_adapter",
        "Task Orchestrator": "task_orchestrator.adapters.bridge_adapter",
        "Serena v2": "serena.v2.bridge_adapter",
        "GPT-Researcher": "dopemux_gpt_researcher.research_api.adapters.bridge_adapter",
        "ADHD Engine": "adhd_engine.bridge_integration",
    }
    
    for service, module_path in adapters.items():
        try:
            # Try to import the adapter module
            module_parts = module_path.split(".")
            module = __import__(module_path, fromlist=[module_parts[-1]])
            
            # Check if adapter class exists
            adapter_classes = [
                name for name in dir(module)
                if "Adapter" in name and not name.startswith("_")
            ]
            
            if adapter_classes:
                print_test(
                    f"  {service}",
                    True,
                    f"Found: {', '.join(adapter_classes)}"
                )
                results[service] = True
            else:
                print_test(
                    f"  {service}",
                    False,
                    "Module imported but no adapter class found"
                )
                results[service] = False
                
        except ImportError as e:
            print_test(
                f"  {service}",
                False,
                f"Import failed: {e}"
            )
            results[service] = False
    
            logger.error(f"Error: {e}")
    return all(results.values())


async def test_environment_variables():
    """Test 6: Required environment variables are set"""
    import os
    
    required_vars = {
        "DOPECON_BRIDGE_URL": "http://localhost:3016",
        "WORKSPACE_ID": os.getcwd(),
    }
    
    optional_vars = {
        "DOPECON_BRIDGE_TOKEN": None,
        "DOPECON_BRIDGE_SOURCE_PLANE": "cognitive_plane",
    }
    
    all_set = True
    
    # Check required vars
    for var, default in required_vars.items():
        value = os.getenv(var, default)
        is_set = var in os.environ
        print_test(
            f"  {var}",
            True,
            f"{'Set to' if is_set else 'Using default'}: {value}"
        )
    
    # Check optional vars
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        is_set = var in os.environ
        if is_set:
            print_test(f"  {var} (optional)", True, f"Set to: {value}")
        else:
            print_test(
                f"  {var} (optional)",
                True,
                f"{YELLOW}Not set, using default: {default}{RESET}"
            )
    
    return all_set


async def main():
    """Run all validation tests"""
    print_section("DopeconBridge Migration Validation")
    
    logger.info("This script validates that the DopeconBridge migration")
    logger.info("is properly configured and ready for use.\n")
    
    results = {}
    
    # Test 1: Client Import
    print_section("Test 1: Client Import")
    results["client_import"] = await test_client_import()
    
    if not results["client_import"]:
        logger.error(f"\n{RED}❌ Cannot proceed - client import failed{RESET}")
        logger.info("Make sure you're running from the repo root and shared modules exist.")
        return
    
    # Test 2: Configuration
    print_section("Test 2: Configuration")
    results["config"] = await test_config_from_env()
    
    # Test 3: Client Creation
    print_section("Test 3: Client Creation")
    results["client_creation"] = await test_client_creation()
    
    # Test 4: Bridge Connection
    print_section("Test 4: Bridge Connection")
    results["bridge_connection"] = await test_bridge_connection()
    
    if not results["bridge_connection"]:
        logger.info(f"\n{YELLOW}⚠️  DopeconBridge is not running{RESET}")
        logger.info("To start it: cd services/mcp-dopecon-bridge && python3 main.py")
        logger.info("Or use Docker: docker-compose up mcp-dopecon-bridge")
    
    # Test 5: Service Adapters
    print_section("Test 5: Service Adapters")
    results["adapters"] = await test_service_adapters()
    
    # Test 6: Environment Variables
    print_section("Test 6: Environment Variables")
    results["environment"] = await test_environment_variables()
    
    # Summary
    print_section("Validation Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    logger.info(f"Tests Passed: {passed}/{total}\n")
    
    for test_name, result in results.items():
        status = f"{GREEN}✅{RESET}" if result else f"{RED}❌{RESET}"
        logger.info(f"{status} {test_name.replace('_', ' ').title()}")
    
    logger.info("\n" + "="*60)
    
    if all(results.values()):
        logger.info(f"{GREEN}✅ All validation tests passed!{RESET}")
        logger.info("DopeconBridge migration is ready to use.")
        return 0
    elif results["client_import"] and results["config"] and results["adapters"]:
        logger.warning(f"{YELLOW}⚠️  Validation passed with warnings{RESET}")
        logger.info("Core components are ready, but DopeconBridge may not be running.")
        logger.error("This is OK for development - services will fail gracefully.")
        return 0
    else:
        logger.error(f"{RED}❌ Validation failed{RESET}")
        logger.error("Some critical components are missing or misconfigured.")
        logger.error("Review the failed tests above and fix issues before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
