"""
TwoPlaneOrchestrator - Two-Plane Architecture Enforcement Agent

Coordinates between PM plane (Leantime) and Cognitive plane (AI agents)
via DopeconBridge. Enforces authority boundaries and routes cross-plane
requests correctly.

Authority: Cross-plane coordination and boundary enforcement

Week: 6
Complexity: 0.6 (Medium-High)
Effort: 5 days (10 focus blocks)
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Plane(str, Enum):
    """Two planes in Dopemux architecture."""
    PM = "pm"  # Project Management plane (Leantime)
    COGNITIVE = "cognitive"  # AI/Cognitive plane (Agents)


class RequestType(str, Enum):
    """Cross-plane request types."""
    QUERY = "query"  # Read-only data request
    COMMAND = "command"  # State-changing operation
    EVENT = "event"  # Notification/signal


@dataclass
class CrossPlaneRequest:
    """Request from one plane to another."""
    id: str
    source_plane: Plane
    target_plane: Plane
    request_type: RequestType
    operation: str  # e.g., "get_tasks", "update_status"
    data: Dict[str, Any]
    timestamp: datetime
    requester: str  # Agent or service name
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class AuthorityRule:
    """Authority matrix rule for data ownership."""
    data_type: str  # e.g., "tasks", "decisions", "adhd_state"
    authority_plane: Plane  # Which plane is the source of truth
    read_allowed_from: List[Plane]  # Planes that can read
    write_allowed_from: List[Plane]  # Planes that can write
    workspace_path: Optional[str] = None  # Multi-workspace tracking


class TwoPlaneOrchestrator:
    """
    Two-Plane Architecture Coordinator.

    Responsibilities:
    1. Route cross-plane requests through DopeconBridge
    2. Validate against authority matrix (warn on violations)
    3. Log cross-plane communication for debugging
    4. Prevent authority boundary violations
    5. Enable ADHD-aware cross-plane workflows

    Example:
        orchestrator = TwoPlaneOrchestrator(
            workspace_id="/path/to/project",
            bridge_url="http://localhost:3016"
        )
        await orchestrator.initialize()

        # Route request from Cognitive to PM plane
        response = await orchestrator.route_request(
            source_plane=Plane.COGNITIVE,
            target_plane=Plane.PM,
            operation="update_task_status",
            data={"task_id": "123", "status": "done"}
        )
    """

    def __init__(
        self,
        workspace_id: str,
        bridge_url: str = "http://localhost:3016",
        conport_client: Optional[Any] = None,
        strict_mode: bool = False
    ):
        """
        Initialize TwoPlaneOrchestrator.

        Args:
            workspace_id: Absolute path to workspace
            bridge_url: DopeconBridge URL
            conport_client: ConPort MCP client for logging
            strict_mode: If True, BLOCK violations (default: warn only)
        """
        self.workspace_id = workspace_id
        self.bridge_url = bridge_url.rstrip('/')
        self.conport_client = conport_client
        self.strict_mode = strict_mode

        # DopeconBridge client
        self.bridge_client: Optional[Any] = None

        # Authority matrix (loaded from Configuration 3.0)
        self.authority_matrix: Dict[str, AuthorityRule] = {}

        # Metrics
        self.metrics = {
            "cross_plane_requests": 0,
            "authority_violations": 0,
            "successful_routes": 0,
            "failed_routes": 0
        }

        # Request tracking (for debugging)
        self.recent_requests: List[CrossPlaneRequest] = []
        self.max_recent = 100  # Keep last 100 requests

        logger.info(
            f"TwoPlaneOrchestrator initialized (bridge: {bridge_url}, "
            f"strict: {strict_mode})"
        )

    async def initialize(self):
        """Initialize DopeconBridge connection and authority matrix."""
        logger.info("🚀 Initializing TwoPlaneOrchestrator...")

        # Initialize DopeconBridge client
        await self._initialize_bridge_client()

        # Load authority matrix
        await self._load_authority_matrix()

        logger.info("✅ TwoPlaneOrchestrator ready for cross-plane coordination")

    async def _initialize_bridge_client(self):
        """Initialize connection to DopeconBridge."""
        try:
            import aiohttp

            self.bridge_client = aiohttp.ClientSession(
                base_url=self.bridge_url,
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # Test connection
            async with self.bridge_client.get("/health") as response:
                if response.status == 200:
                    logger.info(f"🔗 Connected to DopeconBridge ({self.bridge_url})")
                else:
                    logger.warning(f"⚠️ Bridge health check failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to connect to DopeconBridge: {e}")
            logger.warning("⚠️ Cross-plane routing will be degraded")
            self.bridge_client = None

    async def _load_authority_matrix(self):
        """
        Load authority matrix from Configuration 3.0.

        Authority matrix defines which plane is the source of truth for each data type.
        """
        # Authority Matrix (from Architecture 3.0 Configuration)
        self.authority_matrix = {
            "tasks": AuthorityRule(
                data_type="tasks",
                authority_plane=Plane.PM,  # Leantime is authority
                read_allowed_from=[Plane.PM, Plane.COGNITIVE],
                write_allowed_from=[Plane.PM]  # Only PM can write tasks
            ),
            "decisions": AuthorityRule(
                data_type="decisions",
                authority_plane=Plane.COGNITIVE,  # ConPort is authority
                read_allowed_from=[Plane.PM, Plane.COGNITIVE],
                write_allowed_from=[Plane.COGNITIVE]  # Only Cognitive writes decisions
            ),
            "adhd_state": AuthorityRule(
                data_type="adhd_state",
                authority_plane=Plane.COGNITIVE,  # ADHD Engine is authority
                read_allowed_from=[Plane.PM, Plane.COGNITIVE],
                write_allowed_from=[Plane.COGNITIVE]
            ),
            "progress": AuthorityRule(
                data_type="progress",
                authority_plane=Plane.COGNITIVE,  # ConPort is authority
                read_allowed_from=[Plane.PM, Plane.COGNITIVE],
                write_allowed_from=[Plane.COGNITIVE]
            ),
            "sprint_data": AuthorityRule(
                data_type="sprint_data",
                authority_plane=Plane.PM,  # Leantime is authority
                read_allowed_from=[Plane.PM, Plane.COGNITIVE],
                write_allowed_from=[Plane.PM]
            )
        }

        logger.info(f"📋 Authority matrix loaded ({len(self.authority_matrix)} rules)")

    async def route_request(
        self,
        source_plane: Plane,
        target_plane: Plane,
        operation: str,
        data: Dict[str, Any],
        requester: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Route cross-plane request through DopeconBridge.

        Args:
            source_plane: Originating plane
            target_plane: Destination plane
            operation: Operation to perform (e.g., "get_tasks")
            data: Request data
            requester: Name of requesting agent/service

        Returns:
            Response from target plane or error

        Raises:
            ValueError: If strict_mode=True and authority violation detected
        """
        # Create request object
        request = CrossPlaneRequest(
            id=f"{source_plane.value}-{target_plane.value}-{datetime.now().timestamp()}",
            source_plane=source_plane,
            target_plane=target_plane,
            request_type=self._infer_request_type(operation),
            operation=operation,
            data=data,
            timestamp=datetime.now(timezone.utc),
            requester=requester
        )

        # Track request
        self.recent_requests.append(request)
        if len(self.recent_requests) > self.max_recent:
            self.recent_requests.pop(0)
        self.metrics["cross_plane_requests"] += 1

        logger.info(
            f"🔄 Cross-plane request: {source_plane.value} → {target_plane.value} "
            f"({operation})"
        )

        # Validate authority
        validation = await self._validate_authority(request)
        if not validation["valid"]:
            self.metrics["authority_violations"] += 1

            # Log violation to ConPort (if client available)
            if self.conport_client:
                try:
                    await self._log_authority_violation_to_conport(request, validation)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to log violation to ConPort: {e}")

            if self.strict_mode:
                logger.error(f"🚫 Authority violation blocked: {validation['reason']}")
                raise ValueError(f"Authority violation: {validation['reason']}")
            else:
                logger.warning(f"⚠️ Authority violation (allowed): {validation['reason']}")

        # Route through DopeconBridge
        try:
            response = await self._send_through_bridge(request)
            self.metrics["successful_routes"] += 1
            return response

        except Exception as e:
            self.metrics["failed_routes"] += 1
            logger.error(f"❌ Cross-plane routing failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "fallback": "degraded mode"
            }

    def _infer_request_type(self, operation: str) -> RequestType:
        """Infer request type from operation name."""
        if operation.startswith("get_") or operation.startswith("query_"):
            return RequestType.QUERY
        elif operation.startswith("update_") or operation.startswith("set_"):
            return RequestType.COMMAND
        elif operation.endswith("_event") or "notify" in operation:
            return RequestType.EVENT
        else:
            return RequestType.COMMAND  # Default to command

    async def _validate_authority(
        self,
        request: CrossPlaneRequest
    ) -> Dict[str, bool]:
        """
        Validate request against authority matrix.

        Returns:
            {valid: bool, reason: str}
        """
        # Extract data type from operation
        # e.g., "update_task_status" → "tasks"
        data_type = self._extract_data_type(request.operation)

        if data_type not in self.authority_matrix:
            # Unknown data type - allow by default (warn)
            return {
                "valid": True,
                "reason": f"Unknown data type: {data_type} (allowed)"
            }

        rule = self.authority_matrix[data_type]

        # Check read vs write permission
        if request.request_type == RequestType.QUERY:
            # Read operation
            if request.source_plane in rule.read_allowed_from:
                return {"valid": True, "reason": "Read allowed"}
            else:
                return {
                    "valid": False,
                    "reason": f"{request.source_plane.value} cannot read {data_type} "
                            f"(authority: {rule.authority_plane.value})"
                }

        elif request.request_type == RequestType.COMMAND:
            # Write operation
            if request.source_plane in rule.write_allowed_from:
                return {"valid": True, "reason": "Write allowed"}
            else:
                return {
                    "valid": False,
                    "reason": f"{request.source_plane.value} cannot write {data_type} "
                            f"(authority: {rule.authority_plane.value})"
                }

        else:  # EVENT
            # Events allowed from any plane
            return {"valid": True, "reason": "Event allowed"}

    def _extract_data_type(self, operation: str) -> str:
        """Extract data type from operation name."""
        # Simple heuristic: look for known data types in operation
        operation_lower = operation.lower()

        if "task" in operation_lower:
            return "tasks"
        elif "decision" in operation_lower:
            return "decisions"
        elif "adhd" in operation_lower or "cognitive" in operation_lower:
            return "adhd_state"
        elif "progress" in operation_lower:
            return "progress"
        elif "sprint" in operation_lower:
            return "sprint_data"
        else:
            return "unknown"

    async def _log_authority_violation_to_conport(
        self,
        request: CrossPlaneRequest,
        validation: Dict[str, Any]
    ):
        """
        Log authority violation to ConPort for debugging and analysis.

        Week 6 Enhancement: Track cross-plane authority violations
        for compliance monitoring and debugging.
        """
        try:
            # Use log_custom_data for violation tracking
            violation_data = {
                "request_id": request.id,
                "source_plane": request.source_plane.value,
                "target_plane": request.target_plane.value,
                "operation": request.operation,
                "request_type": request.request_type.value,
                "requester": request.requester,
                "violation_reason": validation["reason"],
                "blocked": self.strict_mode,
                "timestamp": request.timestamp.isoformat()
            }

            # Log to ConPort custom_data category: "authority_violations"
            await self.conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category="authority_violations",
                key=request.id,
                value=violation_data
            )

            logger.info(f"📝 Authority violation logged to ConPort: {request.id}")

        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(f"Failed to log violation to ConPort: {e}")
            raise  # Re-raise for caller to handle

    async def _send_through_bridge(
        self,
        request: CrossPlaneRequest
    ) -> Dict[str, Any]:
        """
        Send request through DopeconBridge with retry logic.

        DopeconBridge handles:
        - Event routing between planes
        - Data transformation
        - Async communication

        Week 6 Enhancements:
        - Retry logic (3 attempts, exponential backoff)
        - Graceful degradation on failures
        - Detailed error logging
        """
        if not self.bridge_client:
            # Degraded mode: direct return
            logger.warning("⚠️ No bridge client - returning mock response")
            return {
                "success": True,
                "mode": "degraded",
                "data": {}
            }

        # Retry configuration
        max_retries = 3
        base_delay = 0.5  # seconds

        for attempt in range(max_retries):
            try:
                # POST request to bridge
                endpoint = f"/route/{request.target_plane.value}"

                payload = {
                    "source": request.source_plane.value,
                    "operation": request.operation,
                    "data": request.data,
                    "requester": request.requester
                }

                async with self.bridge_client.post(endpoint, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Log success metrics
                        if attempt > 0:
                            logger.info(
                                f"✅ Request succeeded on attempt {attempt + 1}/{max_retries}"
                            )

                        return result
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Bridge error ({response.status}): {error_text}"
                        )

                        # Don't retry on 4xx client errors (except 429)
                        if 400 <= response.status < 500 and response.status != 429:
                            return {
                                "success": False,
                                "error": f"Bridge returned {response.status}: {error_text}"
                            }

                        # Retry on 5xx server errors or 429
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(
                                f"⚠️ Retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": f"Bridge returned {response.status} after {max_retries} attempts"
                            }

            except asyncio.TimeoutError:
                logger.error(f"⏱️ Request timeout (attempt {attempt + 1}/{max_retries})")

                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final timeout - fall back to degraded mode
                    logger.warning("⚠️ Bridge timeout - switching to degraded mode")
                    return {
                        "success": True,
                        "mode": "degraded",
                        "data": {},
                        "warning": f"Bridge timeout after {max_retries} attempts"
                    }

            except Exception as e:
                logger.error(f"Bridge communication error (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Final failure - fall back to degraded mode
                    logger.warning("⚠️ Bridge unreachable - switching to degraded mode")
                    return {
                        "success": True,
                        "mode": "degraded",
                        "data": {},
                        "error": str(e)
                    }

        # Should never reach here, but just in case
        return {
            "success": False,
            "error": "Unknown error in bridge communication"
        }

    async def get_authority_compliance_report(self) -> Dict[str, Any]:
        """
        Generate authority compliance report.

        Returns:
            Report with violation counts and compliance percentage
        """
        total_requests = self.metrics["cross_plane_requests"]
        violations = self.metrics["authority_violations"]

        compliance_rate = 0.0
        if total_requests > 0:
            compliance_rate = ((total_requests - violations) / total_requests) * 100

        # Analyze violation patterns
        violation_patterns = {}
        for request in self.recent_requests:
            validation = await self._validate_authority(request)
            if not validation["valid"]:
                reason = validation["reason"]
                violation_patterns[reason] = violation_patterns.get(reason, 0) + 1

        return {
            "total_requests": total_requests,
            "successful_routes": self.metrics["successful_routes"],
            "failed_routes": self.metrics["failed_routes"],
            "authority_violations": violations,
            "compliance_rate": compliance_rate,
            "violation_patterns": violation_patterns,
            "strict_mode": self.strict_mode
        }

    async def pm_to_cognitive(
        self,
        operation: str,
        data: Dict[str, Any],
        requester: str = "leantime"
    ) -> Dict[str, Any]:
        """
        Convenience method: Route PM → Cognitive request.

        Use for: PM plane needs AI agent capabilities
        Examples: Get code complexity, run analysis, generate decisions
        """
        return await self.route_request(
            source_plane=Plane.PM,
            target_plane=Plane.COGNITIVE,
            operation=operation,
            data=data,
            requester=requester
        )

    async def cognitive_to_pm(
        self,
        operation: str,
        data: Dict[str, Any],
        requester: str = "agent"
    ) -> Dict[str, Any]:
        """
        Convenience method: Route Cognitive → PM request.

        Use for: Agents need PM data or update PM state
        Examples: Get tasks, update task status, create subtasks
        """
        return await self.route_request(
            source_plane=Plane.COGNITIVE,
            target_plane=Plane.PM,
            operation=operation,
            data=data,
            requester=requester
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of TwoPlaneOrchestrator and DopeconBridge connection.

        Week 6 Enhancement: Production health monitoring
        """
        health_status = {
            "orchestrator": "healthy",
            "bridge_connected": self.bridge_client is not None,
            "conport_connected": self.conport_client is not None,
            "strict_mode": self.strict_mode,
            "metrics": self.metrics.copy(),
            "authority_rules": len(self.authority_matrix),
            "recent_requests_count": len(self.recent_requests)
        }

        # Test bridge connectivity
        if self.bridge_client:
            try:
                async with self.bridge_client.get("/health") as response:
                    if response.status == 200:
                        health_status["bridge_status"] = "healthy"
                    else:
                        health_status["bridge_status"] = f"unhealthy ({response.status})"
            except Exception as e:
                health_status["bridge_status"] = f"unreachable ({str(e)})"
        else:
            health_status["bridge_status"] = "not_configured"

        return health_status

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get detailed metrics summary with compliance analysis.

        Week 6 Enhancement: Production metrics and observability
        """
        total_requests = self.metrics["cross_plane_requests"]
        violations = self.metrics["authority_violations"]
        successful = self.metrics["successful_routes"]
        failed = self.metrics["failed_routes"]

        # Calculate rates
        compliance_rate = 0.0
        success_rate = 0.0

        if total_requests > 0:
            compliance_rate = ((total_requests - violations) / total_requests) * 100
            success_rate = (successful / total_requests) * 100

        # Analyze request patterns
        request_by_plane = {
            "pm_to_cognitive": 0,
            "cognitive_to_pm": 0
        }

        for req in self.recent_requests:
            if req.source_plane == Plane.PM and req.target_plane == Plane.COGNITIVE:
                request_by_plane["pm_to_cognitive"] += 1
            elif req.source_plane == Plane.COGNITIVE and req.target_plane == Plane.PM:
                request_by_plane["cognitive_to_pm"] += 1

        return {
            "total_requests": total_requests,
            "successful_routes": successful,
            "failed_routes": failed,
            "authority_violations": violations,
            "compliance_rate": round(compliance_rate, 2),
            "success_rate": round(success_rate, 2),
            "request_patterns": request_by_plane,
            "strict_mode": self.strict_mode
        }

    async def close(self):
        """Shutdown orchestrator and close connections."""
        logger.info("🛑 Shutting down TwoPlaneOrchestrator...")

        if self.bridge_client:
            await self.bridge_client.close()

        logger.info("✅ TwoPlaneOrchestrator shutdown complete")


# ============================================================================
# Demo / Test
# ============================================================================

async def demo():
    """Demonstrate TwoPlaneOrchestrator."""

    print("\n" + "="*70)
    print("TWO-PLANE ORCHESTRATOR DEMO")
    print("="*70)

    # Create orchestrator
    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3016",
        strict_mode=False  # Warn only, don't block
    )

    await orchestrator.initialize()

    print("\n📋 Authority Matrix Loaded:")
    for data_type, rule in orchestrator.authority_matrix.items():
        print(f"\n  {data_type}:")
        print(f"    Authority: {rule.authority_plane.value}")
        print(f"    Read: {[p.value for p in rule.read_allowed_from]}")
        print(f"    Write: {[p.value for p in rule.write_allowed_from]}")

    # Example 1: Cognitive → PM (query tasks)
    print("\n" + "="*70)
    print("Example 1: Cognitive → PM (Get Tasks)")
    print("="*70)

    response = await orchestrator.cognitive_to_pm(
        operation="get_tasks",
        data={"status": "TODO"},
        requester="MemoryAgent"
    )

    print(f"\nResponse: {response}")

    # Example 2: PM → Cognitive (query complexity)
    print("\n" + "="*70)
    print("Example 2: PM → Cognitive (Get Code Complexity)")
    print("="*70)

    response = await orchestrator.pm_to_cognitive(
        operation="get_complexity",
        data={"file": "auth.py", "function": "login"},
        requester="Leantime"
    )

    print(f"\nResponse: {response}")

    # Example 3: Authority violation (PM tries to write decision)
    print("\n" + "="*70)
    print("Example 3: Authority Violation (PM → Write Decision)")
    print("="*70)

    try:
        response = await orchestrator.pm_to_cognitive(
            operation="update_decision",  # WRITE to decisions
            data={"decision_id": "123", "status": "approved"},
            requester="Leantime"
        )
        print(f"\nResponse: {response}")
    except ValueError as e:
        print(f"\n🚫 Blocked (strict mode): {e}")

    # Compliance report
    print("\n" + "="*70)
    print("Authority Compliance Report")
    print("="*70)

    report = await orchestrator.get_authority_compliance_report()

    print(f"\nTotal Requests: {report['total_requests']}")
    print(f"Successful Routes: {report['successful_routes']}")
    print(f"Failed Routes: {report['failed_routes']}")
    print(f"Authority Violations: {report['authority_violations']}")
    print(f"Compliance Rate: {report['compliance_rate']:.1f}%")
    print(f"Strict Mode: {report['strict_mode']}")

    if report['violation_patterns']:
        print(f"\nViolation Patterns:")
        for pattern, count in report['violation_patterns'].items():
            print(f"  - {pattern}: {count}x")

    # Cleanup
    await orchestrator.close()

    print("\n" + "="*70)
    print("✅ Demo complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
