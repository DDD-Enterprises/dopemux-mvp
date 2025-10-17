# Implementation Plan: Integration Bridge Completion

**Task ID**: IP-002
**Priority**: 🔴 CRITICAL
**Duration**: 9 days (18 focus blocks @ 25min each)
**Complexity**: 0.75 (HIGH)
**Dependencies**: None (can run parallel with IP-001)
**Risk Level**: HIGH (requires careful event bus design)

---

## Executive Summary

**Problem**: Integration Bridge designed as event orchestrator but only has 5 read-only GET endpoints. No cross-service coordination exists.

**Solution**: Complete Integration Bridge with pub/sub event bus, cross-service task routing, and MCP-to-MCP communication patterns.

**Impact**:
- ✅ Enables MCP-to-MCP communication (currently isolated)
- ✅ Activates Redis event bus for cross-service coordination
- ✅ Implements event orchestration for two-plane architecture
- ✅ Unlocks true system integration capabilities

**Success Criteria**:
- [ ] Event bus operational (publish/subscribe working)
- [ ] MCP services can communicate through Integration Bridge
- [ ] Task routing decisions flow across services
- [ ] Events logged and traceable
- [ ] PM ↔ Cognitive plane coordination functional

---

## Current State Analysis

###

 Existing Integration Bridge (services/integration-bridge/)

**Current Endpoints** (minimal functionality):
```python
# Only 5 read-only GET endpoints exist:
GET /health                    # Health check
GET /services                  # List registered services
GET /tasks/{task_id}          # Get task details
GET /contexts/{context_id}    # Get context
GET /status                    # System status
```

**Missing Critical Functionality**:
- ❌ No POST/PUT endpoints for events
- ❌ No pub/sub event bus implementation
- ❌ No cross-service task routing
- ❌ No MCP-to-MCP communication handlers
- ❌ No event orchestration logic
- ❌ No authority enforcement for cross-plane calls

**What Research Spec Says** (from ARCHITECTURE-CONSOLIDATION-SYNTHESIS.md):

> "Integration Bridge designed as event orchestrator with pub/sub coordination, cross-service task routing, and authority enforcement. Currently dormant with only 5 read-only endpoints."

---

## Architecture Design

### Event Bus Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTEGRATION BRIDGE                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              EVENT BUS (Redis Pub/Sub)                   │  │
│  │                                                          │  │
│  │  Channels:                                               │  │
│  │    - dopemux:events:task_routed                         │  │
│  │    - dopemux:events:decision_logged                     │  │
│  │    - dopemux:events:context_switched                    │  │
│  │    - dopemux:events:adhd_state_changed                  │  │
│  │    - dopemux:events:mcp_request                         │  │
│  │    - dopemux:events:mcp_response                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                EVENT ORCHESTRATOR                        │  │
│  │                                                          │  │
│  │  - Event validation and schema checking                 │  │
│  │  - Authority enforcement (PM vs Cognitive)              │  │
│  │  - Event routing to subscribers                         │  │
│  │  - Event logging and tracing                            │  │
│  │  - Circuit breaker patterns                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MCP SERVICE REGISTRY                        │  │
│  │                                                          │  │
│  │  Registered Services:                                    │  │
│  │    - ConPort MCP (port 3004, Cognitive plane)           │  │
│  │    - Serena MCP (stdio, Cognitive plane)                │  │
│  │    - dope-context MCP (stdio, Cognitive plane)          │  │
│  │    - ADHD Engine (internal, Cognitive plane)            │  │
│  │    - Task-Master (port 3005, PM plane)                  │  │
│  │    - Task-Orchestrator (port 3006, PM plane)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
           ▲                      ▲                      ▲
           │                      │                      │
      ┌────┴─────┐         ┌─────┴──────┐        ┌─────┴──────┐
      │ ConPort  │         │   Serena   │        │Task-Master │
      │   MCP    │         │    MCP     │        │     AI     │
      └──────────┘         └────────────┘        └────────────┘
```

### Event Types & Schemas

```python
# Event type definitions
class EventType(str, Enum):
    # Task events (PM plane)
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_ROUTED = "task.routed"

    # Context events (Cognitive plane)
    CONTEXT_SWITCHED = "context.switched"
    DECISION_LOGGED = "decision.logged"
    PATTERN_DISCOVERED = "pattern.discovered"

    # ADHD events (Cognitive plane)
    ADHD_STATE_CHANGED = "adhd.state_changed"
    ENERGY_LEVEL_UPDATED = "adhd.energy_updated"
    BREAK_RECOMMENDED = "adhd.break_recommended"

    # Cross-service events
    MCP_REQUEST = "mcp.request"
    MCP_RESPONSE = "mcp.response"
    INTEGRATION_ERROR = "integration.error"

# Event schema
@dataclass
class IntegrationEvent:
    event_id: str                    # UUID
    event_type: EventType
    source_service: str              # Which service published
    target_service: Optional[str]    # Specific target (or None for broadcast)
    timestamp: datetime
    plane: str                       # "PM" or "Cognitive"
    payload: Dict[str, Any]
    trace_id: Optional[str]          # For distributed tracing
    requires_response: bool = False
```

---

## Day-by-Day Implementation Plan

### Day 1: Event Bus Infrastructure (2 focus blocks, 50min)

**Location**: `services/integration-bridge/event_bus/` (NEW DIRECTORY)

**Tasks**:
1. Create Redis pub/sub client
2. Implement EventPublisher and EventSubscriber classes
3. Add event serialization/deserialization
4. Write unit tests

**Code** (`event_bus/redis_event_bus.py`):
```python
"""
Redis-based Event Bus for Integration Bridge
"""
import asyncio
import json
import logging
import redis.asyncio as redis
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from uuid import uuid4

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_ROUTED = "task.routed"
    CONTEXT_SWITCHED = "context.switched"
    DECISION_LOGGED = "decision.logged"
    PATTERN_DISCOVERED = "pattern.discovered"
    ADHD_STATE_CHANGED = "adhd.state_changed"
    ENERGY_LEVEL_UPDATED = "adhd.energy_updated"
    BREAK_RECOMMENDED = "adhd.break_recommended"
    MCP_REQUEST = "mcp.request"
    MCP_RESPONSE = "mcp.response"
    INTEGRATION_ERROR = "integration.error"

@dataclass
class IntegrationEvent:
    """Event schema for Integration Bridge."""
    event_id: str
    event_type: EventType
    source_service: str
    target_service: Optional[str]
    timestamp: str
    plane: str  # "PM" or "Cognitive"
    payload: Dict[str, Any]
    trace_id: Optional[str] = None
    requires_response: bool = False

    def to_json(self) -> str:
        """Serialize event to JSON."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'IntegrationEvent':
        """Deserialize event from JSON."""
        data = json.loads(json_str)
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)


class RedisEventBus:
    """
    Redis pub/sub event bus for Integration Bridge.

    Provides publish/subscribe messaging for cross-service coordination.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/6"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False

    async def initialize(self) -> None:
        """Initialize Redis connections."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis_client.ping()
        self.pubsub = self.redis_client.pubsub()
        logger.info("✅ Event Bus initialized")

    async def publish(self, event: IntegrationEvent) -> None:
        """
        Publish event to Redis channel.

        Channel naming: dopemux:events:{event_type}
        """
        channel = f"dopemux:events:{event.event_type.value}"

        # Log event for tracing
        await self._log_event(event)

        # Publish to channel
        await self.redis_client.publish(channel, event.to_json())

        logger.info(f"📤 Published {event.event_type.value} from {event.source_service}")

    async def subscribe(
        self,
        event_type: EventType,
        handler: Callable[[IntegrationEvent], None]
    ) -> None:
        """
        Subscribe to specific event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async function to call when event received
        """
        channel = f"dopemux:events:{event_type.value}"

        # Register handler
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(handler)

        # Subscribe to Redis channel
        await self.pubsub.subscribe(channel)

        logger.info(f"📥 Subscribed to {event_type.value}")

    async def start_listening(self) -> None:
        """
        Start listening for events (background task).

        Call this in asyncio.create_task() to run continuously.
        """
        self.running = True
        logger.info("👂 Event Bus listening for events...")

        try:
            async for message in self.pubsub.listen():
                if not self.running:
                    break

                if message['type'] == 'message':
                    await self._handle_message(message)

        except Exception as e:
            logger.error(f"Event Bus error: {e}")
        finally:
            self.running = False

    async def stop(self) -> None:
        """Stop listening and cleanup."""
        self.running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("🛑 Event Bus stopped")

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming Redis message."""
        try:
            channel = message['channel']
            event_json = message['data']

            # Deserialize event
            event = IntegrationEvent.from_json(event_json)

            # Call registered handlers
            handlers = self.subscribers.get(channel, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type}: {e}")

        except Exception as e:
            logger.error(f"Message handling error: {e}")

    async def _log_event(self, event: IntegrationEvent) -> None:
        """Log event to Redis for tracing/debugging."""
        log_key = f"dopemux:event_log:{datetime.now().strftime('%Y-%m-%d')}"

        log_entry = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "source": event.source_service,
            "target": event.target_service,
            "timestamp": event.timestamp,
            "trace_id": event.trace_id
        }

        await self.redis_client.lpush(log_key, json.dumps(log_entry))

        # Keep only last 1000 events per day
        await self.redis_client.ltrim(log_key, 0, 999)

        # Expire after 7 days
        await self.redis_client.expire(log_key, 7 * 24 * 60 * 60)


# Global singleton
_event_bus: Optional[RedisEventBus] = None

async def get_event_bus(redis_url: str = "redis://localhost:6379/6") -> RedisEventBus:
    """Get or create global EventBus instance."""
    global _event_bus

    if _event_bus is None:
        _event_bus = RedisEventBus(redis_url)
        await _event_bus.initialize()

    return _event_bus
```

**Tests** (`tests/test_event_bus.py`):
```python
import pytest
from event_bus.redis_event_bus import RedisEventBus, IntegrationEvent, EventType
from datetime import datetime

@pytest.mark.asyncio
async def test_publish_subscribe():
    """Test basic pub/sub functionality."""
    bus = RedisEventBus()
    await bus.initialize()

    # Track received events
    received_events = []

    async def handler(event: IntegrationEvent):
        received_events.append(event)

    # Subscribe to event type
    await bus.subscribe(EventType.TASK_CREATED, handler)

    # Start listening in background
    import asyncio
    listener_task = asyncio.create_task(bus.start_listening())

    # Publish event
    test_event = IntegrationEvent(
        event_id=str(uuid4()),
        event_type=EventType.TASK_CREATED,
        source_service="test",
        target_service=None,
        timestamp=datetime.now().isoformat(),
        plane="PM",
        payload={"task_id": "123", "title": "Test Task"}
    )

    await bus.publish(test_event)

    # Wait for delivery
    await asyncio.sleep(0.1)

    # Verify received
    assert len(received_events) == 1
    assert received_events[0].event_id == test_event.event_id

    # Cleanup
    await bus.stop()
    listener_task.cancel()
```

**Deliverables**:
- [ ] Redis event bus implemented
- [ ] Pub/sub working
- [ ] Event serialization tested
- [ ] Event logging operational

---

### Day 2-3: Event Orchestrator (4 focus blocks, 100min)

**Location**: `services/integration-bridge/event_orchestrator.py` (NEW FILE)

**Tasks**:
1. Create EventOrchestrator class
2. Implement authority enforcement (PM vs Cognitive)
3. Add event validation and schema checking
4. Add circuit breaker patterns
5. Write tests

**Code** (`event_orchestrator.py`):
```python
"""
Event Orchestrator for Integration Bridge

Coordinates cross-service events with authority enforcement.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from event_bus.redis_event_bus import (
    RedisEventBus,
    IntegrationEvent,
    EventType,
    get_event_bus
)

logger = logging.getLogger(__name__)

@dataclass
class ServiceRegistration:
    """Registered service in Integration Bridge."""
    service_name: str
    plane: str  # "PM" or "Cognitive"
    endpoint: Optional[str]  # HTTP endpoint or None for stdio
    health_check_url: Optional[str]
    last_heartbeat: datetime

class EventOrchestrator:
    """
    Event orchestration engine for Integration Bridge.

    Responsibilities:
    - Event routing with authority enforcement
    - Cross-plane communication validation
    - Circuit breaker patterns
    - Event tracing and logging
    """

    def __init__(self, event_bus: RedisEventBus):
        self.event_bus = event_bus
        self.registered_services: Dict[str, ServiceRegistration] = {}
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}

        # Authority matrix: Which plane can access which events
        self.pm_plane_services = {"task-master", "task-orchestrator", "leantime"}
        self.cognitive_plane_services = {"conport", "serena", "dope-context", "adhd-engine"}

    async def initialize(self) -> None:
        """Initialize orchestrator and register event handlers."""
        # Subscribe to all event types for orchestration
        await self.event_bus.subscribe(EventType.TASK_CREATED, self._handle_task_event)
        await self.event_bus.subscribe(EventType.TASK_ROUTED, self._handle_task_event)
        await self.event_bus.subscribe(EventType.DECISION_LOGGED, self._handle_decision_event)
        await self.event_bus.subscribe(EventType.ADHD_STATE_CHANGED, self._handle_adhd_event)
        await self.event_bus.subscribe(EventType.MCP_REQUEST, self._handle_mcp_request)

        logger.info("✅ Event Orchestrator initialized")

    def register_service(
        self,
        service_name: str,
        plane: str,
        endpoint: Optional[str] = None,
        health_check_url: Optional[str] = None
    ) -> None:
        """Register a service in the Integration Bridge."""
        service = ServiceRegistration(
            service_name=service_name,
            plane=plane,
            endpoint=endpoint,
            health_check_url=health_check_url,
            last_heartbeat=datetime.now()
        )

        self.registered_services[service_name] = service
        logger.info(f"✅ Registered {service_name} ({plane} plane)")

    async def publish_event(self, event: IntegrationEvent) -> None:
        """
        Publish event with authority validation.

        Enforces two-plane architecture boundaries.
        """
        # Validate source service is registered
        if event.source_service not in self.registered_services:
            logger.warning(f"⚠️ Unregistered service: {event.source_service}")
            return

        source_service = self.registered_services[event.source_service]

        # Authority enforcement
        if not self._validate_authority(source_service, event):
            logger.error(f"❌ Authority violation: {event.source_service} cannot publish {event.event_type}")
            return

        # Check circuit breaker
        if self._is_circuit_open(event.source_service):
            logger.warning(f"⚠️ Circuit breaker open for {event.source_service}")
            return

        # Publish event
        await self.event_bus.publish(event)

        # Update circuit breaker (success)
        self._record_success(event.source_service)

    def _validate_authority(
        self,
        source: ServiceRegistration,
        event: IntegrationEvent
    ) -> bool:
        """
        Validate service has authority to publish event type.

        PM Plane can publish:
        - task.* events (task management)

        Cognitive Plane can publish:
        - decision.* events
        - pattern.* events
        - adhd.* events
        - context.* events

        Cross-plane events require special validation.
        """
        # PM plane authority
        if source.plane == "PM":
            pm_events = {EventType.TASK_CREATED, EventType.TASK_UPDATED, EventType.TASK_COMPLETED, EventType.TASK_ROUTED}
            return event.event_type in pm_events

        # Cognitive plane authority
        if source.plane == "Cognitive":
            cognitive_events = {
                EventType.DECISION_LOGGED,
                EventType.PATTERN_DISCOVERED,
                EventType.CONTEXT_SWITCHED,
                EventType.ADHD_STATE_CHANGED,
                EventType.ENERGY_LEVEL_UPDATED,
                EventType.BREAK_RECOMMENDED
            }
            return event.event_type in cognitive_events

        # Cross-plane events (MCP_REQUEST/MCP_RESPONSE) allowed from both
        if event.event_type in {EventType.MCP_REQUEST, EventType.MCP_RESPONSE}:
            return True

        return False

    async def _handle_task_event(self, event: IntegrationEvent) -> None:
        """Handle task-related events from PM plane."""
        logger.info(f"🎯 Task event: {event.event_type} from {event.source_service}")

        # Route to Cognitive plane services if task needs code context
        if "requires_code_context" in event.payload and event.payload["requires_code_context"]:
            # Notify Serena to prepare code context
            await self._notify_service("serena", event)

        # Log decision if task routing decision made
        if event.event_type == EventType.TASK_ROUTED:
            await self._log_routing_decision(event)

    async def _handle_decision_event(self, event: IntegrationEvent) -> None:
        """Handle decision-logged events from Cognitive plane."""
        logger.info(f"📋 Decision logged: {event.event_type} from {event.source_service}")

        # Notify PM plane if decision impacts task planning
        if "impacts_tasks" in event.payload and event.payload["impacts_tasks"]:
            await self._notify_service("task-orchestrator", event)

    async def _handle_adhd_event(self, event: IntegrationEvent) -> None:
        """Handle ADHD state change events."""
        logger.info(f"🧠 ADHD event: {event.event_type}")

        # Broadcast ADHD state changes to all Cognitive plane services
        for service_name, service in self.registered_services.items():
            if service.plane == "Cognitive":
                await self._notify_service(service_name, event)

    async def _handle_mcp_request(self, event: IntegrationEvent) -> None:
        """Handle MCP-to-MCP communication requests."""
        logger.info(f"🔗 MCP request: {event.source_service} → {event.target_service}")

        # Validate target service exists
        if event.target_service not in self.registered_services:
            logger.error(f"❌ Target service not found: {event.target_service}")
            return

        # Forward request to target service
        await self._notify_service(event.target_service, event)

    async def _notify_service(self, service_name: str, event: IntegrationEvent) -> None:
        """Notify specific service of event."""
        if service_name not in self.registered_services:
            logger.warning(f"⚠️ Service not registered: {service_name}")
            return

        service = self.registered_services[service_name]

        # Create notification event
        notification = IntegrationEvent(
            event_id=str(uuid4()),
            event_type=EventType.MCP_REQUEST,
            source_service="integration-bridge",
            target_service=service_name,
            timestamp=datetime.now().isoformat(),
            plane=service.plane,
            payload={"original_event": event.to_json()}
        )

        # Publish notification
        await self.event_bus.publish(notification)

    async def _log_routing_decision(self, event: IntegrationEvent) -> None:
        """Log task routing decisions to ConPort."""
        # Create decision log event
        decision_event = IntegrationEvent(
            event_id=str(uuid4()),
            event_type=EventType.DECISION_LOGGED,
            source_service="integration-bridge",
            target_service="conport",
            timestamp=datetime.now().isoformat(),
            plane="Cognitive",
            payload={
                "decision_type": "task_routing",
                "task_id": event.payload.get("task_id"),
                "routed_to": event.payload.get("assigned_service"),
                "rationale": event.payload.get("routing_rationale")
            }
        )

        await self.event_bus.publish(decision_event)

    # Circuit breaker implementation

    def _is_circuit_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()

        return self.circuit_breakers[service_name].is_open()

    def _record_success(self, service_name: str) -> None:
        """Record successful event for circuit breaker."""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].record_success()

    def _record_failure(self, service_name: str) -> None:
        """Record failed event for circuit breaker."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()

        self.circuit_breakers[service_name].record_failure()


class CircuitBreaker:
    """
    Circuit breaker pattern for service protection.

    Prevents cascading failures by temporarily blocking requests
    to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests)."""
        if self.state == "CLOSED":
            return False

        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                if (datetime.now() - self.last_failure_time).total_seconds() > self.timeout_seconds:
                    self.state = "HALF_OPEN"
                    return False
            return True

        # HALF_OPEN state - allow one request through
        return False

    def record_success(self) -> None:
        """Record successful operation."""
        if self.state == "HALF_OPEN":
            # Recovery successful, close circuit
            self.state = "CLOSED"
            self.failure_count = 0
            self.last_failure_time = None

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"⚠️ Circuit breaker opened after {self.failure_count} failures")
```

**Deliverables**:
- [ ] Event orchestrator implemented
- [ ] Authority enforcement working
- [ ] Circuit breakers operational
- [ ] Cross-plane validation tested

---

### Day 4-5: REST API Endpoints (4 focus blocks, 100min)

**Location**: `services/integration-bridge/api/events.py` (NEW FILE)

**Tasks**:
1. Add POST /events endpoint (publish events)
2. Add GET /events endpoint (query event history)
3. Add POST /subscribe endpoint (webhook subscriptions)
4. Add health checks and metrics
5. Test API

**Code** (`api/events.py`):
```python
"""
REST API for Integration Bridge Event System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from event_orchestrator import EventOrchestrator
from event_bus.redis_event_bus import IntegrationEvent, EventType, get_event_bus

app = FastAPI(title="Integration Bridge API")

# Global orchestrator instance
orchestrator: Optional[EventOrchestrator] = None

@app.on_event("startup")
async def startup():
    """Initialize Integration Bridge on startup."""
    global orchestrator

    event_bus = await get_event_bus()
    orchestrator = EventOrchestrator(event_bus)
    await orchestrator.initialize()

    # Register existing services
    orchestrator.register_service("conport", "Cognitive", "http://localhost:3004")
    orchestrator.register_service("serena", "Cognitive")
    orchestrator.register_service("dope-context", "Cognitive")
    orchestrator.register_service("adhd-engine", "Cognitive")
    orchestrator.register_service("task-master", "PM", "http://localhost:3005")
    orchestrator.register_service("task-orchestrator", "PM", "http://localhost:3006")

    # Start event bus listener
    import asyncio
    asyncio.create_task(event_bus.start_listening())

    logger.info("✅ Integration Bridge API ready")

# Pydantic models for API

class PublishEventRequest(BaseModel):
    event_type: str
    source_service: str
    target_service: Optional[str] = None
    plane: str
    payload: Dict[str, Any]
    trace_id: Optional[str] = None

class EventQueryRequest(BaseModel):
    event_type: Optional[str] = None
    source_service: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100

# API Endpoints

@app.post("/events")
async def publish_event(request: PublishEventRequest):
    """
    Publish event to Integration Bridge.

    Authority validation and routing handled by EventOrchestrator.
    """
    try:
        event = IntegrationEvent(
            event_id=str(uuid4()),
            event_type=EventType(request.event_type),
            source_service=request.source_service,
            target_service=request.target_service,
            timestamp=datetime.now().isoformat(),
            plane=request.plane,
            payload=request.payload,
            trace_id=request.trace_id
        )

        await orchestrator.publish_event(event)

        return {
            "status": "published",
            "event_id": event.event_id,
            "timestamp": event.timestamp
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")

@app.get("/events")
async def query_events(request: EventQueryRequest):
    """
    Query event history from Redis logs.

    Useful for debugging and tracing.
    """
    try:
        redis_client = orchestrator.event_bus.redis_client

        # Get today's event log
        log_key = f"dopemux:event_log:{datetime.now().strftime('%Y-%m-%d')}"
        events_json = await redis_client.lrange(log_key, 0, request.limit - 1)

        events = [json.loads(e) for e in events_json]

        # Apply filters
        if request.event_type:
            events = [e for e in events if e['event_type'] == request.event_type]
        if request.source_service:
            events = [e for e in events if e['source'] == request.source_service]

        return {
            "events": events,
            "count": len(events),
            "queried_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query events: {str(e)}")

@app.get("/services")
async def list_services():
    """List all registered services."""
    services = []
    for name, service in orchestrator.registered_services.items():
        services.append({
            "name": name,
            "plane": service.plane,
            "endpoint": service.endpoint,
            "last_heartbeat": service.last_heartbeat.isoformat()
        })

    return {"services": services}

@app.post("/services/register")
async def register_service(
    service_name: str,
    plane: str,
    endpoint: Optional[str] = None,
    health_check_url: Optional[str] = None
):
    """Register a new service with Integration Bridge."""
    orchestrator.register_service(service_name, plane, endpoint, health_check_url)

    return {
        "status": "registered",
        "service_name": service_name,
        "plane": plane
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "event_bus_connected": orchestrator.event_bus.redis_client is not None,
        "registered_services": len(orchestrator.registered_services),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics."""
    # Count events from today's log
    redis_client = orchestrator.event_bus.redis_client
    log_key = f"dopemux:event_log:{datetime.now().strftime('%Y-%m-%d')}"
    event_count = await redis_client.llen(log_key)

    return {
        "events_published_today": event_count,
        "registered_services": len(orchestrator.registered_services),
        "circuit_breakers_open": sum(
            1 for cb in orchestrator.circuit_breakers.values() if cb.is_open()
        )
    }
```

**Deliverables**:
- [ ] POST /events endpoint working
- [ ] GET /events query working
- [ ] Service registration API operational
- [ ] Health checks and metrics exposed

---

### Day 6-7: MCP Client Integration (4 focus blocks, 100min)

**Tasks**:
1. Add event publishing to ConPort MCP
2. Add event publishing to Serena MCP
3. Add event subscribers to both
4. Test cross-MCP communication

**ConPort Integration** (`services/conport/src/context_portal_mcp/integration_bridge_client.py`):
```python
"""
Integration Bridge Client for ConPort MCP
"""
import httpx
from typing import Dict, Any, Optional

class IntegrationBridgeClient:
    """
    Client for ConPort to publish events to Integration Bridge.
    """

    def __init__(self, bridge_url: str = "http://localhost:3016"):
        self.bridge_url = bridge_url
        self.client = httpx.AsyncClient()

    async def publish_decision_logged(
        self,
        decision_id: int,
        summary: str,
        rationale: str
    ) -> None:
        """Publish decision.logged event."""
        event = {
            "event_type": "decision.logged",
            "source_service": "conport",
            "target_service": None,  # Broadcast
            "plane": "Cognitive",
            "payload": {
                "decision_id": decision_id,
                "summary": summary,
                "rationale": rationale
            }
        }

        try:
            response = await self.client.post(f"{self.bridge_url}/events", json=event)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to publish decision event: {e}")

    async def publish_pattern_discovered(
        self,
        pattern_id: int,
        pattern_name: str,
        description: str
    ) -> None:
        """Publish pattern.discovered event."""
        event = {
            "event_type": "pattern.discovered",
            "source_service": "conport",
            "target_service": None,
            "plane": "Cognitive",
            "payload": {
                "pattern_id": pattern_id,
                "pattern_name": pattern_name,
                "description": description
            }
        }

        try:
            response = await self.client.post(f"{self.bridge_url}/events", json=event)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to publish pattern event: {e}")
```

**Integrate into ConPort handlers** (`services/conport/src/context_portal_mcp/handlers/mcp_handlers.py`):
```python
# Add to handle_log_decision()
async def handle_log_decision(params: Dict[str, Any]) -> Dict[str, Any]:
    # Existing decision logging code...

    # NEW: Publish event to Integration Bridge
    bridge_client = IntegrationBridgeClient()
    await bridge_client.publish_decision_logged(
        decision_id=decision_id,
        summary=params['summary'],
        rationale=params['rationale']
    )

    return result
```

**Serena Integration**: Similar pattern

**Deliverables**:
- [ ] ConPort publishes decision events
- [ ] Serena publishes navigation events
- [ ] Event subscribers receiving events
- [ ] Cross-MCP communication working

---

### Day 8: Documentation & Testing (2 focus blocks, 50min)

**Tasks**:
1. End-to-end integration tests
2. API documentation (OpenAPI/Swagger)
3. Event flow diagrams
4. Runbook for operations

**Integration Tests** (`tests/integration/test_integration_bridge_e2e.py`):
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_decision_logged_flow():
    """
    Test complete event flow:
    ConPort logs decision → Integration Bridge → Event published → Serena receives
    """
    # 1. ConPort logs decision (via MCP)
    conport_response = await conport_mcp.log_decision(
        summary="Use Redis for event bus",
        rationale="Fast pub/sub with persistence"
    )

    # 2. Check event published to Integration Bridge
    async with httpx.AsyncClient() as client:
        events = await client.get(
            "http://localhost:3016/events",
            params={"event_type": "decision.logged"}
        )

    assert events.status_code == 200
    assert len(events.json()['events']) > 0

    # 3. Verify event received by subscriber
    # (Would check Serena logs or internal state)

    print("✅ Decision logged event flow complete!")

@pytest.mark.asyncio
async def test_adhd_state_broadcast():
    """
    Test ADHD state changes broadcast to all Cognitive plane services.
    """
    # Publish ADHD state change
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:3016/events",
            json={
                "event_type": "adhd.state_changed",
                "source_service": "adhd-engine",
                "target_service": None,  # Broadcast
                "plane": "Cognitive",
                "payload": {
                    "user_id": "developer1",
                    "attention_state": "scattered",
                    "energy_level": "low"
                }
            }
        )

    assert response.status_code == 200

    # Verify all Cognitive services receive event
    # (Check Serena, ConPort, dope-context logs)

    print("✅ ADHD state broadcast successful!")
```

**API Documentation**: Auto-generated with FastAPI Swagger UI at `http://localhost:3016/docs`

**Deliverables**:
- [ ] Integration tests passing
- [ ] API docs generated
- [ ] Event flow diagrams complete
- [ ] Operations runbook ready

---

### Day 9: Rollout & Monitoring (2 focus blocks, 50min)

**Tasks**:
1. Deploy Integration Bridge service
2. Configure monitoring and alerts
3. Enable event publishing gradually
4. Verify event flows operational

**Deployment** (`docker-compose.integration-bridge.yml`):
```yaml
services:
  integration-bridge:
    build: ./services/integration-bridge
    ports:
      - "3016:3016"
    environment:
      - REDIS_URL=redis://dopemux-redis-events:6379/6
    depends_on:
      - dopemux-redis-events
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3016/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Monitoring** (Prometheus + Grafana):
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'integration-bridge'
    static_configs:
      - targets: ['integration-bridge:3016']
    metrics_path: '/metrics'
```

**Grafana Dashboard**:
- Events published per minute
- Event types breakdown
- Cross-service communication graph
- Circuit breaker status
- Authority violations (should be 0)

**Deliverables**:
- [ ] Integration Bridge deployed
- [ ] Monitoring operational
- [ ] Alerts configured
- [ ] Event flows verified
- [ ] Ready for production! 🎉

---

## Success Metrics

**Technical**:
- [ ] Event bus operational (pub/sub working)
- [ ] 6+ event types flowing (task, decision, adhd, mcp)
- [ ] Authority enforcement: 0 violations
- [ ] Circuit breakers protecting services
- [ ] Event latency <10ms

**Integration**:
- [ ] ConPort publishes decision events
- [ ] Serena publishes navigation events
- [ ] ADHD Engine broadcasts state changes
- [ ] Cross-MCP communication working
- [ ] PM ↔ Cognitive coordination functional

**Operational**:
- [ ] Event logging and tracing operational
- [ ] 7-day event history retained
- [ ] Monitoring dashboards showing real-time events
- [ ] Alerts firing on anomalies
- [ ] Zero downtime deployments

---

## Risk Assessment

**Risk 1: Event Storm**
**Probability**: MEDIUM
**Impact**: HIGH
**Mitigation**: Circuit breakers, rate limiting, event sampling

**Risk 2: Authority Bypass**
**Probability**: LOW
**Impact**: CRITICAL
**Mitigation**: Strict validation in EventOrchestrator, audit logging

**Risk 3: Redis Failure**
**Probability**: LOW
**Impact**: HIGH
**Mitigation**: Redis clustering, event persistence to disk, fallback mechanisms

---

## Rollback Plan

**Immediate Rollback**:
```bash
# Stop Integration Bridge
docker-compose stop integration-bridge

# Services automatically fallback to direct communication
# No event bus = isolated services (original state)
```

**Gradual Rollback**:
- Disable event publishing per service
- Keep Integration Bridge running for monitoring
- Re-enable gradually after fixes

---

**Total Effort**: 9 days (18 focus blocks)
**Risk Level**: HIGH (new architecture component)
**Impact**: EXTREME (enables true integration)
**ROI**: 🔥 Very High (unlocks cross-service coordination)
