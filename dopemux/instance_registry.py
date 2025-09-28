"""
Multi-Instance Registry for Dopemux

Manages instance discovery, coordination, and session handoff between instances.
"""

import asyncio
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from enum import Enum

from .event_bus import EventBus, DopemuxEvent, Priority, CognitiveLoad, ADHDMetadata


class InstanceStatus(Enum):
    """Instance operational status."""
    STARTING = "starting"
    ACTIVE = "active"
    IDLE = "idle"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class InstanceInfo:
    """Information about a Dopemux instance."""
    instance_id: str
    port_base: int
    git_worktree_path: str
    git_branch: str
    status: InstanceStatus
    started_at: datetime
    last_heartbeat: datetime

    # Service endpoints
    task_master_url: str
    conport_url: str
    serena_url: Optional[str] = None

    # Capabilities
    capabilities: List[str] = None

    # User context
    current_user: Optional[str] = None
    session_id: Optional[str] = None
    focus_context: str = "general"

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = ["task_management", "memory", "mcp"]


class InstanceRegistry:
    """Registry for managing multiple Dopemux instances."""

    def __init__(self, event_bus: EventBus, workspace_root: str = "/Users/hue/code/dopemux-mvp"):
        self.event_bus = event_bus
        self.workspace_root = workspace_root

        # Instance tracking
        self.instances: Dict[str, InstanceInfo] = {}
        self.port_allocations: Set[int] = set()

        # Event subscriptions
        self.subscription_id: Optional[str] = None

        # Background tasks
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the instance registry service."""
        # Subscribe to instance events
        self.subscription_id = await self.event_bus.subscribe(
            namespace_pattern="global.instance.*",
            callback=self._handle_instance_event,
            consumer_group="instance_registry"
        )

        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())

        # Discover existing instances
        await self._discover_existing_instances()

        print("🏢 Instance Registry started")

    async def stop(self):
        """Stop the instance registry service."""
        if self.subscription_id:
            await self.event_bus.unsubscribe(self.subscription_id)

        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        if self.health_monitor_task:
            self.health_monitor_task.cancel()

        print("🏢 Instance Registry stopped")

    async def register_instance(
        self,
        instance_id: str,
        port_base: int,
        git_branch: str = "main",
        user: Optional[str] = None
    ) -> InstanceInfo:
        """Register a new instance."""
        # Validate instance ID
        if instance_id in self.instances:
            raise ValueError(f"Instance {instance_id} already registered")

        # Check port availability
        if port_base in self.port_allocations:
            raise ValueError(f"Port base {port_base} already allocated")

        # Create instance info
        git_worktree_path = os.path.join(self.workspace_root, f"worktrees/{instance_id}")

        instance = InstanceInfo(
            instance_id=instance_id,
            port_base=port_base,
            git_worktree_path=git_worktree_path,
            git_branch=git_branch,
            status=InstanceStatus.STARTING,
            started_at=datetime.now(),
            last_heartbeat=datetime.now(),
            task_master_url=f"http://localhost:{port_base + 5}",
            conport_url=f"http://localhost:{port_base + 7}",
            serena_url=f"http://localhost:{port_base + 6}",
            current_user=user
        )

        # Register instance
        self.instances[instance_id] = instance
        self.port_allocations.add(port_base)

        # Emit registration event
        await self._emit_instance_event("instance.registered", instance)

        print(f"📝 Registered instance {instance_id} on port base {port_base}")
        return instance

    async def unregister_instance(self, instance_id: str):
        """Unregister an instance."""
        if instance_id not in self.instances:
            return

        instance = self.instances[instance_id]
        instance.status = InstanceStatus.STOPPED

        # Emit unregistration event
        await self._emit_instance_event("instance.unregistered", instance)

        # Clean up
        self.port_allocations.discard(instance.port_base)
        del self.instances[instance_id]

        print(f"🗑️ Unregistered instance {instance_id}")

    async def update_instance_status(self, instance_id: str, status: InstanceStatus):
        """Update instance status."""
        if instance_id not in self.instances:
            return

        instance = self.instances[instance_id]
        old_status = instance.status
        instance.status = status
        instance.last_heartbeat = datetime.now()

        # Emit status change event
        await self._emit_status_change_event(instance, old_status, status)

    async def heartbeat(self, instance_id: str, context: Dict[str, Any] = None):
        """Record instance heartbeat."""
        if instance_id not in self.instances:
            return

        instance = self.instances[instance_id]
        instance.last_heartbeat = datetime.now()

        # Update context if provided
        if context:
            instance.focus_context = context.get("focus_context", instance.focus_context)
            instance.session_id = context.get("session_id", instance.session_id)

    async def request_session_handoff(
        self,
        from_instance: str,
        to_instance: str,
        session_data: Dict[str, Any]
    ) -> bool:
        """Request session handoff between instances."""
        if from_instance not in self.instances or to_instance not in self.instances:
            return False

        from_info = self.instances[from_instance]
        to_info = self.instances[to_instance]

        # Validate instances are ready
        if from_info.status != InstanceStatus.ACTIVE:
            return False

        if to_info.status not in [InstanceStatus.ACTIVE, InstanceStatus.IDLE]:
            return False

        # Emit handoff request event
        await self._emit_handoff_event(from_info, to_info, session_data)

        print(f"🔄 Session handoff requested: {from_instance} → {to_instance}")
        return True

    def get_instance(self, instance_id: str) -> Optional[InstanceInfo]:
        """Get instance information."""
        return self.instances.get(instance_id)

    def get_active_instances(self) -> List[InstanceInfo]:
        """Get all active instances."""
        return [
            instance for instance in self.instances.values()
            if instance.status == InstanceStatus.ACTIVE
        ]

    def get_available_port_base(self) -> int:
        """Get next available port base."""
        base_ports = [3000, 3030, 3060, 3090, 3120]  # Support up to 5 instances

        for port in base_ports:
            if port not in self.port_allocations:
                return port

        raise RuntimeError("No available port bases")

    def suggest_instance_id(self) -> str:
        """Suggest next available instance ID."""
        letters = ['A', 'B', 'C', 'D', 'E']

        for letter in letters:
            if letter not in self.instances:
                return letter

        # Fallback to timestamp-based ID
        return f"I{int(datetime.now().timestamp()) % 1000}"

    async def _discover_existing_instances(self):
        """Discover instances that might already be running."""
        # Check for existing worktrees
        worktrees_dir = os.path.join(self.workspace_root, "worktrees")
        if os.path.exists(worktrees_dir):
            for item in os.listdir(worktrees_dir):
                if os.path.isdir(os.path.join(worktrees_dir, item)):
                    # Found potential instance worktree
                    await self._check_instance_health(item)

    async def _check_instance_health(self, instance_id: str):
        """Check if an instance is actually running."""
        # Try common port bases
        port_bases = [3000, 3030, 3060]

        for port_base in port_bases:
            try:
                # Simple health check - try to connect to task master
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:{port_base + 5}/health",
                        timeout=aiohttp.ClientTimeout(total=2)
                    ) as response:
                        if response.status == 200:
                            # Instance appears to be running
                            await self._register_discovered_instance(instance_id, port_base)
                            break
            except:
                continue  # Instance not running on this port

    async def _register_discovered_instance(self, instance_id: str, port_base: int):
        """Register a discovered running instance."""
        if instance_id in self.instances:
            return

        git_worktree_path = os.path.join(self.workspace_root, f"worktrees/{instance_id}")

        instance = InstanceInfo(
            instance_id=instance_id,
            port_base=port_base,
            git_worktree_path=git_worktree_path,
            git_branch="unknown",  # Would need to detect
            status=InstanceStatus.ACTIVE,
            started_at=datetime.now() - timedelta(minutes=5),  # Estimate
            last_heartbeat=datetime.now(),
            task_master_url=f"http://localhost:{port_base + 5}",
            conport_url=f"http://localhost:{port_base + 7}",
            serena_url=f"http://localhost:{port_base + 6}"
        )

        self.instances[instance_id] = instance
        self.port_allocations.add(port_base)

        print(f"🔍 Discovered running instance {instance_id} on port {port_base}")

    def _handle_instance_event(self, event: DopemuxEvent):
        """Handle incoming instance events."""
        asyncio.create_task(self._async_handle_instance_event(event))

    async def _async_handle_instance_event(self, event: DopemuxEvent):
        """Async handling of instance events."""
        event_type = event.envelope.type
        payload = event.payload

        if event_type == "instance.heartbeat":
            await self.heartbeat(
                payload.get("instance_id"),
                payload.get("context", {})
            )

        elif event_type == "instance.status.changed":
            instance_id = payload.get("instance_id")
            new_status = InstanceStatus(payload.get("new_status"))
            await self.update_instance_status(instance_id, new_status)

        elif event_type == "instance.session.handoff.request":
            await self.request_session_handoff(
                payload.get("from_instance"),
                payload.get("to_instance"),
                payload.get("session_data", {})
            )

    async def _emit_instance_event(self, event_type: str, instance: InstanceInfo):
        """Emit instance-related event."""
        event = DopemuxEvent.create(
            event_type=f"instance.{event_type}",
            namespace="global.instance",
            payload={
                "instance_id": instance.instance_id,
                "port_base": instance.port_base,
                "status": instance.status.value,
                "git_branch": instance.git_branch,
                "capabilities": instance.capabilities,
                "timestamp": datetime.now().isoformat()
            },
            source="instance.registry",
            priority=Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="system_management"
            ),
            targets=["global"],
            filters=["instance.management", "system.coordination"]
        )

        await self.event_bus.publish(event)

    async def _emit_status_change_event(
        self,
        instance: InstanceInfo,
        old_status: InstanceStatus,
        new_status: InstanceStatus
    ):
        """Emit instance status change event."""
        event = DopemuxEvent.create(
            event_type="instance.status.changed",
            namespace="global.instance",
            payload={
                "instance_id": instance.instance_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "timestamp": datetime.now().isoformat()
            },
            source="instance.registry",
            priority=Priority.HIGH if new_status == InstanceStatus.ERROR else Priority.NORMAL,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MEDIUM if new_status == InstanceStatus.ERROR else CognitiveLoad.LOW,
                attention_required=new_status == InstanceStatus.ERROR,
                interruption_safe=new_status != InstanceStatus.ERROR,
                focus_context="system_monitoring"
            ),
            targets=["global"],
            filters=["instance.status", "system.monitoring"]
        )

        await self.event_bus.publish(event)

    async def _emit_handoff_event(
        self,
        from_instance: InstanceInfo,
        to_instance: InstanceInfo,
        session_data: Dict[str, Any]
    ):
        """Emit session handoff event."""
        event = DopemuxEvent.create(
            event_type="instance.session.handoff",
            namespace="shared.session",
            payload={
                "from_instance": from_instance.instance_id,
                "to_instance": to_instance.instance_id,
                "session_data": session_data,
                "handoff_time": datetime.now().isoformat()
            },
            source="instance.registry",
            priority=Priority.HIGH,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.LOW,
                attention_required=False,
                interruption_safe=True,
                focus_context="session_management"
            ),
            targets=["shared.session"],
            filters=["session.handoff", "instance.coordination"]
        )

        await self.event_bus.publish(event)

    async def _heartbeat_loop(self):
        """Background heartbeat monitoring."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                now = datetime.now()
                stale_threshold = now - timedelta(minutes=2)

                for instance in list(self.instances.values()):
                    if instance.last_heartbeat < stale_threshold:
                        if instance.status == InstanceStatus.ACTIVE:
                            # Mark as potentially dead
                            await self.update_instance_status(instance.instance_id, InstanceStatus.ERROR)
                            print(f"⚠️ Instance {instance.instance_id} appears unresponsive")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat monitor error: {e}")

    async def _health_monitor_loop(self):
        """Background health monitoring."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                for instance in self.instances.values():
                    if instance.status in [InstanceStatus.ACTIVE, InstanceStatus.IDLE]:
                        # Emit periodic health status
                        await self._emit_health_status(instance)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health monitor error: {e}")

    async def _emit_health_status(self, instance: InstanceInfo):
        """Emit instance health status."""
        uptime = datetime.now() - instance.started_at

        event = DopemuxEvent.create(
            event_type="instance.health.status",
            namespace="global.instance.health",
            payload={
                "instance_id": instance.instance_id,
                "status": instance.status.value,
                "uptime_minutes": int(uptime.total_seconds() / 60),
                "port_base": instance.port_base,
                "capabilities": instance.capabilities,
                "timestamp": datetime.now().isoformat()
            },
            source="instance.registry",
            priority=Priority.LOW,
            adhd_metadata=ADHDMetadata(
                cognitive_load=CognitiveLoad.MINIMAL,
                attention_required=False,
                interruption_safe=True,
                focus_context="system_monitoring",
                batching_allowed=True
            ),
            targets=["shared.monitoring"],
            filters=["health.monitoring", "system.analytics"]
        )

        await self.event_bus.publish(event)

    def get_registry_status(self) -> Dict[str, Any]:
        """Get registry status information."""
        return {
            "total_instances": len(self.instances),
            "active_instances": len(self.get_active_instances()),
            "allocated_ports": sorted(list(self.port_allocations)),
            "instances": {
                instance_id: {
                    "status": instance.status.value,
                    "port_base": instance.port_base,
                    "uptime_minutes": int((datetime.now() - instance.started_at).total_seconds() / 60),
                    "last_heartbeat": instance.last_heartbeat.isoformat()
                }
                for instance_id, instance in self.instances.items()
            }
        }