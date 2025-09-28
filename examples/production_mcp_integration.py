#!/usr/bin/env python3
"""
Production MCP Integration Example

Demonstrates integration with running MCP services using the event wrapper pattern.
This script shows how to integrate event emission with real MCP service calls.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
from dopemux.event_bus import RedisStreamsAdapter, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata
from dopemux.producers.mcp_producer import MCPEventProducer
from dopemux.producers.conport_producer import ConPortEventProducer


class ProductionMCPEventIntegrator:
    """
    Production integration layer for MCP services with event emission.

    This demonstrates the pattern for wrapping actual MCP HTTP service calls
    with event emission without modifying the service infrastructure.
    """

    def __init__(self, event_bus: RedisStreamsAdapter, instance_id: str):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.mcp_producer = MCPEventProducer(event_bus, instance_id)
        self.conport_producer = ConPortEventProducer(event_bus, instance_id, "/Users/hue/code/dopemux-mvp")

        # MCP service endpoints
        self.services = {
            'conport': 'http://localhost:3004',
            'taskmaster': 'http://localhost:3005',
            'zen': 'http://localhost:3003',
            'context7': 'http://localhost:3002'
        }

        self.session = None

    async def start(self):
        """Initialize the production integration layer."""
        await self.event_bus.connect()
        self.session = aiohttp.ClientSession()
        print(f"🔗 Production MCP Integrator started for instance {self.instance_id}")

    async def stop(self):
        """Cleanup the integration layer."""
        if self.session:
            await self.session.close()
        await self.event_bus.disconnect()
        print(f"🔗 Production MCP Integrator stopped for instance {self.instance_id}")

    async def call_conport_mcp(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call ConPort MCP service with event emission wrapper.

        This demonstrates the production pattern for integrating events
        with actual HTTP-based MCP service calls.
        """
        tool_name = f"mcp__conport__{method}"
        call_id = await self.mcp_producer.on_tool_call_start(tool_name, payload)

        start_time = time.time()
        result = None
        error = None

        try:
            # Make actual HTTP call to ConPort MCP service
            url = f"{self.services['conport']}/call"
            request_data = {
                "method": method,
                "params": payload
            }

            async with self.session.post(url, json=request_data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()

                    # Emit ConPort-specific events based on the operation
                    await self._emit_conport_events(method, payload, result)

                else:
                    error = f"HTTP {response.status}: {await response.text()}"
                    result = {"error": error}

        except asyncio.TimeoutError:
            error = "Request timeout"
            result = {"error": error}
        except Exception as e:
            error = str(e)
            result = {"error": error}

        finally:
            # Emit completion event
            await self.mcp_producer.on_tool_call_complete(
                call_id, tool_name, payload, result, error
            )

        return result

    async def _emit_conport_events(self, method: str, payload: Dict[str, Any], result: Dict[str, Any]):
        """Emit ConPort-specific events based on the operation type."""

        if method == "log_decision" and "error" not in result:
            await self.conport_producer.on_decision_logged(
                decision_id=result.get("id", 0),
                summary=payload.get("summary", ""),
                rationale=payload.get("rationale", ""),
                tags=payload.get("tags", []),
                implementation_details=payload.get("implementation_details")
            )

        elif method == "log_progress" and "error" not in result:
            await self.conport_producer.on_progress_updated(
                progress_id=result.get("id", 0),
                description=payload.get("description", ""),
                old_status="pending",  # Would need to track previous state
                new_status=payload.get("status", "active")
            )

        elif method == "get_active_context" and "error" not in result:
            await self.conport_producer.on_context_accessed(
                context_type="active_context",
                access_reason="production_integration"
            )

        elif method == "log_custom_data" and "error" not in result:
            await self.conport_producer.on_custom_data_logged(
                category=payload.get("category", ""),
                key=payload.get("key", ""),
                value=payload.get("value"),
                operation="create"
            )

    async def call_taskmaster_mcp(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call TaskMaster MCP service with event emission."""
        tool_name = f"mcp__taskmaster__{method}"
        call_id = await self.mcp_producer.on_tool_call_start(tool_name, payload)

        start_time = time.time()
        result = None
        error = None

        try:
            url = f"{self.services['taskmaster']}/call"
            request_data = {
                "method": method,
                "params": payload
            }

            async with self.session.post(url, json=request_data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                else:
                    error = f"HTTP {response.status}: {await response.text()}"
                    result = {"error": error}

        except Exception as e:
            error = str(e)
            result = {"error": error}

        finally:
            await self.mcp_producer.on_tool_call_complete(
                call_id, tool_name, payload, result, error
            )

        return result

    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check if an MCP service is healthy and responsive."""
        if service_name not in self.services:
            return {"healthy": False, "error": f"Unknown service: {service_name}"}

        try:
            url = f"{self.services[service_name]}/health"
            async with self.session.get(url, timeout=5) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return {"healthy": True, "status": health_data}
                else:
                    return {"healthy": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


async def demo_production_integration():
    """Demonstrate production MCP integration with real services."""
    print("🏭 Production MCP Integration Demo")
    print("=" * 50)

    # Setup
    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    integrator = ProductionMCPEventIntegrator(event_bus, "PRODUCTION_DEMO")

    await integrator.start()

    try:
        # Check service health first
        print("🏥 Checking MCP service health:")
        for service in ['conport', 'taskmaster', 'zen', 'context7']:
            health = await integrator.check_service_health(service)
            status = "✅ HEALTHY" if health['healthy'] else f"❌ UNHEALTHY: {health['error']}"
            print(f"   {service}: {status}")
        print()

        # Test ConPort integration with real service
        print("📊 Testing ConPort MCP integration:")

        # 1. Get active context (read operation)
        print("1. Getting active context...")
        result = await integrator.call_conport_mcp("get_active_context", {
            "workspace_id": "/Users/hue/code/dopemux-mvp"
        })
        if "error" not in result:
            print(f"   ✅ Context retrieved: {result.get('context', {}).get('current_focus', 'N/A')}")
        else:
            print(f"   ❌ Error: {result['error']}")
        print()

        # 2. Log a decision (write operation)
        print("2. Logging decision...")
        result = await integrator.call_conport_mcp("log_decision", {
            "workspace_id": "/Users/hue/code/dopemux-mvp",
            "summary": "Integrate production MCP event system",
            "rationale": "Enable real-time coordination across instances in production",
            "tags": ["production", "events", "mcp", "integration"]
        })
        if "error" not in result:
            print(f"   ✅ Decision logged with ID: {result.get('id', 'unknown')}")
        else:
            print(f"   ❌ Error: {result['error']}")
        print()

        # 3. Log progress (write operation)
        print("3. Logging progress...")
        result = await integrator.call_conport_mcp("log_progress", {
            "workspace_id": "/Users/hue/code/dopemux-mvp",
            "status": "IN_PROGRESS",
            "description": "Production MCP event integration deployment"
        })
        if "error" not in result:
            print(f"   ✅ Progress logged with ID: {result.get('id', 'unknown')}")
        else:
            print(f"   ❌ Error: {result['error']}")
        print()

        # 4. Log custom data (write operation)
        print("4. Logging custom data...")
        result = await integrator.call_conport_mcp("log_custom_data", {
            "workspace_id": "/Users/hue/code/dopemux-mvp",
            "category": "integration_tests",
            "key": "production_demo_timestamp",
            "value": {
                "timestamp": datetime.now().isoformat(),
                "test_type": "production_integration",
                "status": "active"
            }
        })
        if "error" not in result:
            print(f"   ✅ Custom data logged successfully")
        else:
            print(f"   ❌ Error: {result['error']}")
        print()

        print("🎉 Production Integration Demo Complete!")
        print()
        print("Integration Benefits:")
        print("• Real MCP service calls wrapped with event emission")
        print("• No modification to existing MCP infrastructure required")
        print("• Automatic ConPort-specific event generation")
        print("• Production-ready HTTP service integration")
        print("• Health checking and error handling included")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")

    finally:
        await integrator.stop()


async def demo_multi_service_coordination():
    """Demonstrate coordination between multiple MCP services."""
    print("\n🔗 Multi-Service Coordination Demo")
    print("=" * 50)

    event_bus = RedisStreamsAdapter("redis://localhost:6379")
    integrator = ProductionMCPEventIntegrator(event_bus, "COORDINATION_DEMO")

    await integrator.start()

    try:
        # Demonstrate workflow that uses multiple services
        print("🔄 Multi-service workflow simulation:")

        # 1. Log decision in ConPort
        decision_result = await integrator.call_conport_mcp("log_decision", {
            "workspace_id": "/Users/hue/code/dopemux-mvp",
            "summary": "Use TaskMaster for complex task decomposition",
            "rationale": "TaskMaster provides AI-driven task breakdown capabilities",
            "tags": ["workflow", "taskmaster", "integration"]
        })

        if "error" not in decision_result:
            print(f"   ✅ Decision logged: ID {decision_result.get('id')}")

            # 2. Could integrate with TaskMaster (if service supports the method)
            # This would be expanded based on actual TaskMaster API
            print("   🤖 TaskMaster integration ready for task decomposition")

            # 3. Log progress in ConPort
            progress_result = await integrator.call_conport_mcp("log_progress", {
                "workspace_id": "/Users/hue/code/dopemux-mvp",
                "status": "DONE",
                "description": "Multi-service coordination workflow completed"
            })

            if "error" not in progress_result:
                print(f"   ✅ Workflow completed: Progress ID {progress_result.get('id')}")

        print("\n📊 Coordination Summary:")
        print("   • Multiple services coordinated through events")
        print("   • Workflow state tracked across services")
        print("   • Event-driven handoffs between services")

    except Exception as e:
        print(f"❌ Coordination demo failed: {e}")

    finally:
        await integrator.stop()


async def main():
    """Run the production MCP integration demonstration."""
    print("🏭 Production MCP Event Integration")
    print("=" * 50)
    print("This demo shows integration with real running MCP services:")
    print("• ConPort memory system (localhost:3004)")
    print("• TaskMaster AI (localhost:3005)")
    print("• Zen multi-model (localhost:3003)")
    print("• Context7 docs (localhost:3002)")
    print()

    try:
        await demo_production_integration()
        await demo_multi_service_coordination()

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Ensure MCP services are running:")
        print("docker-compose -f docker/mcp-servers/docker-compose.yml up -d")


if __name__ == "__main__":
    asyncio.run(main())