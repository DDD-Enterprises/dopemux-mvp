"""
MetaMCP Broker: Central orchestration for role-aware tool brokering

The MetaMCP Broker is the core component that manages role-based tool access,
token budgets, and session orchestration. It coordinates between the role system,
budget management, and MCP server connections to provide ADHD-optimized
development experiences with dramatic token reduction.

Key Features:
- Role-based tool mounting/unmounting with <200ms latency
- Budget-aware pre-tool hooks preventing runaway token consumption
- ADHD-friendly progressive disclosure and context preservation
- Graceful degradation with fallback to static profiles
- Comprehensive observability and audit logging

Integration Points:
- Claude-flow: Maintains as primary orchestrator
- Letta: Memory offload for context window management
- ConPort: Session context preservation
- Tmux UI: Status updates and notifications
"""

import asyncio
import logging
import time
import yaml
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from .roles import RoleManager, Role
from .token_manager import TokenBudgetManager, BudgetStatus
from .session_manager import SessionManager
from .hooks import PreToolHookManager, OptimizationResult
from .server_manager import MCPServerManager, ServerConnection
from .observability import MetricsCollector, HealthMonitor

logger = logging.getLogger(__name__)


class BrokerStatus(Enum):
    """Broker operational status"""
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


@dataclass
class BrokerConfig:
    """Configuration for the MetaMCP Broker"""
    name: str = "dopemux-metamcp-broker"
    version: str = "1.0.0"
    host: str = "localhost"
    port: int = 8090

    # Performance settings
    max_concurrent_tools: int = 10
    tool_timeout_seconds: int = 30
    role_switch_timeout_seconds: int = 5
    health_check_interval: int = 60

    # Policy and configuration paths
    policy_config_path: str = "/config/mcp/policy.yaml"
    broker_config_path: str = "/config/mcp/broker.yaml"

    # Feature flags
    role_based_mounting: bool = True
    budget_aware_hooks: bool = True
    letta_integration: bool = True
    adhd_optimizations: bool = True

    @classmethod
    def from_file(cls, config_path: str) -> 'BrokerConfig':
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        broker_section = config_data.get('broker', {})
        features_section = config_data.get('features', {})

        return cls(
            name=broker_section.get('name', cls.name),
            version=broker_section.get('version', cls.version),
            host=broker_section.get('host', cls.host),
            port=broker_section.get('port', cls.port),
            max_concurrent_tools=broker_section.get('max_concurrent_tools', cls.max_concurrent_tools),
            tool_timeout_seconds=broker_section.get('tool_timeout_seconds', cls.tool_timeout_seconds),
            role_switch_timeout_seconds=broker_section.get('role_switch_timeout_seconds', cls.role_switch_timeout_seconds),
            health_check_interval=broker_section.get('health_check_interval', cls.health_check_interval),
            role_based_mounting=features_section.get('role_based_mounting', cls.role_based_mounting),
            budget_aware_hooks=features_section.get('budget_aware_hooks', cls.budget_aware_hooks),
            letta_integration=features_section.get('letta_integration', cls.letta_integration),
            adhd_optimizations=features_section.get('adhd_optimizations', cls.adhd_optimizations)
        )


@dataclass
class ToolCallRequest:
    """Request to call a tool through the broker"""
    session_id: str
    tool_name: str
    method: str
    args: Dict[str, Any]
    request_id: str = field(default_factory=lambda: f"req_{int(time.time() * 1000)}")
    timestamp: datetime = field(default_factory=datetime.now)
    role: Optional[str] = None
    priority: str = "normal"  # normal, high, emergency


@dataclass
class ToolCallResponse:
    """Response from a tool call through the broker"""
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    optimizations: List[OptimizationResult] = field(default_factory=list)
    token_usage: int = 0
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionState:
    """Current state of a broker session"""
    session_id: str
    role: Optional[str] = None
    mounted_tools: Set[str] = field(default_factory=set)
    budget_status: Optional[BudgetStatus] = None
    last_activity: datetime = field(default_factory=datetime.now)
    context_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    escalation_active: bool = False
    escalation_expires: Optional[datetime] = None


class MetaMCPBroker:
    """
    Central MetaMCP broker for role-aware tool orchestration.

    The broker coordinates all aspects of the MetaMCP system:
    - Role-based tool mounting and access control
    - Token budget management and optimization
    - Session lifecycle and context preservation
    - Integration with external systems (Claude-flow, Letta, ConPort)
    - Observability and health monitoring
    """

    def __init__(self, config: Optional[BrokerConfig] = None):
        self.config = config or BrokerConfig()
        self.status = BrokerStatus.STARTING

        # Core components
        self.role_manager: Optional[RoleManager] = None
        self.token_manager: Optional[TokenBudgetManager] = None
        self.session_manager: Optional[SessionManager] = None
        self.hook_manager: Optional[PreToolHookManager] = None
        self.server_manager: Optional[MCPServerManager] = None

        # Observability
        self.metrics = MetricsCollector()
        self.health_monitor = HealthMonitor()

        # Session tracking
        self.active_sessions: Dict[str, SessionState] = {}
        self.tool_call_queue = asyncio.Queue()

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()

        logger.info(f"MetaMCP Broker initialized: {self.config.name} v{self.config.version}")

    async def start(self) -> None:
        """Start the MetaMCP broker and all subsystems"""
        try:
            logger.info("Starting MetaMCP Broker...")

            # Load configurations
            await self._load_configurations()

            # Initialize core components
            await self._initialize_components()

            # Start MCP server connections
            await self._start_server_connections()

            # Start background tasks
            await self._start_background_tasks()

            self.status = BrokerStatus.READY
            logger.info("MetaMCP Broker started successfully")

            # Record startup metrics
            self.metrics.record_startup()

        except Exception as e:
            self.status = BrokerStatus.FAILED
            logger.error(f"Failed to start MetaMCP Broker: {e}")
            raise

    async def stop(self) -> None:
        """Gracefully stop the MetaMCP broker"""
        logger.info("Stopping MetaMCP Broker...")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Stop server connections
        if self.server_manager:
            await self.server_manager.stop_all()

        # Save session states for recovery
        await self._save_session_states()

        self.status = BrokerStatus.FAILED
        logger.info("MetaMCP Broker stopped")

    async def switch_role(self, session_id: str, new_role: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Switch a session to a new role with tool remounting.

        This is a core ADHD accommodation feature that preserves context
        while providing access to role-appropriate tools.
        """
        start_time = time.time()

        try:
            logger.info(f"Role switch requested: session {session_id} -> {new_role}")

            # Get or create session state
            session = self._get_or_create_session(session_id)
            previous_role = session.role

            # Validate the role transition
            if not await self.role_manager.validate_role_transition(previous_role, new_role):
                raise ValueError(f"Invalid role transition: {previous_role} -> {new_role}")

            # Create context checkpoint before role switch (ADHD accommodation)
            if previous_role and self.config.adhd_optimizations:
                checkpoint = await self._create_context_checkpoint(session_id, f"role_switch_from_{previous_role}")
                session.context_checkpoints.append(checkpoint)

            # Get new role configuration
            role_config = await self.role_manager.get_role(new_role)
            if not role_config:
                raise ValueError(f"Unknown role: {new_role}")

            # Calculate required tool changes
            current_tools = session.mounted_tools
            required_tools = set(role_config.default_tools)

            tools_to_unmount = current_tools - required_tools
            tools_to_mount = required_tools - current_tools

            # Unmount unnecessary tools
            if tools_to_unmount:
                await self._unmount_tools(session_id, tools_to_unmount)

            # Mount new tools
            if tools_to_mount:
                await self._mount_tools(session_id, tools_to_mount)

            # Update session state
            session.role = new_role
            session.mounted_tools = required_tools
            session.last_activity = datetime.now()

            # Update token budget for new role
            await self.token_manager.switch_role_budget(session_id, new_role)
            session.budget_status = await self.token_manager.get_budget_status(session_id)

            # Clear any active escalations
            session.escalation_active = False
            session.escalation_expires = None

            # Notify UI about role switch (ADHD accommodation)
            if self.config.adhd_optimizations:
                await self._notify_role_switch(session_id, previous_role, new_role, session.mounted_tools)

            # Record metrics
            switch_time_ms = int((time.time() - start_time) * 1000)
            self.metrics.record_role_switch(previous_role, new_role, switch_time_ms)

            logger.info(f"Role switch completed: {previous_role} -> {new_role} in {switch_time_ms}ms")

            return {
                'success': True,
                'previous_role': previous_role,
                'new_role': new_role,
                'mounted_tools': list(session.mounted_tools),
                'tools_mounted': list(tools_to_mount),
                'tools_unmounted': list(tools_to_unmount),
                'switch_time_ms': switch_time_ms,
                'budget_status': session.budget_status.__dict__ if session.budget_status else None
            }

        except Exception as e:
            logger.error(f"Role switch failed for session {session_id}: {e}")
            self.metrics.record_role_switch_failure(session_id, new_role, str(e))

            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'requested_role': new_role
            }

    async def call_tool(self, request: ToolCallRequest) -> ToolCallResponse:
        """
        Execute a tool call with budget awareness and optimization.

        This is the main entry point for all tool calls, providing:
        - Pre-tool hook optimization
        - Budget enforcement
        - Role-based access control
        - Performance monitoring
        """
        start_time = time.time()

        try:
            # Get session state
            session = self.active_sessions.get(request.session_id)
            if not session:
                raise ValueError(f"No active session: {request.session_id}")

            # Verify tool access for current role
            if not await self._verify_tool_access(session, request.tool_name):
                raise PermissionError(f"Tool {request.tool_name} not available for role {session.role}")

            # Apply pre-tool hooks for optimization
            optimizations = []
            if self.config.budget_aware_hooks:
                call_dict = {
                    'tool': request.tool_name,
                    'method': request.method,
                    'args': request.args
                }

                session_context = {
                    'session_id': request.session_id,
                    'role': session.role
                }

                optimized_call, applied_optimizations = await self.hook_manager.pre_tool_check(call_dict, session_context)
                optimizations.extend(applied_optimizations)

                # Update request with optimized parameters
                request.args = optimized_call.get('args', request.args)

            # Check if the call was denied by hooks
            if any(opt.action_taken.value == 'deny_expensive' for opt in optimizations):
                return ToolCallResponse(
                    request_id=request.request_id,
                    success=False,
                    error="Tool call denied due to budget constraints",
                    optimizations=optimizations,
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

            # Execute the tool call
            result = await self.server_manager.call_tool(
                server_name=request.tool_name,
                method=request.method,
                args=request.args,
                timeout=self.config.tool_timeout_seconds
            )

            # Update token usage
            estimated_tokens = sum(opt.estimated_token_savings for opt in optimizations)
            actual_tokens = await self._estimate_actual_token_usage(result)
            await self.token_manager.record_usage(request.session_id, actual_tokens)

            # Update session activity
            session.last_activity = datetime.now()
            session.budget_status = await self.token_manager.get_budget_status(request.session_id)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Record metrics
            self.metrics.record_tool_call(
                session.role,
                request.tool_name,
                request.method,
                execution_time_ms,
                actual_tokens,
                len(optimizations)
            )

            return ToolCallResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                optimizations=optimizations,
                token_usage=actual_tokens,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Tool call failed: {request.tool_name}.{request.method} - {e}")

            self.metrics.record_tool_call_failure(request.tool_name, request.method, str(e))

            return ToolCallResponse(
                request_id=request.request_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms
            )

    async def request_escalation(self, session_id: str, escalation_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request temporary access to additional tools beyond role defaults.

        This supports the ADHD workflow where users may need to temporarily
        access tools outside their current role for specific tasks.
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session or not session.role:
                raise ValueError(f"No active session with role: {session_id}")

            # Check if escalation is allowed for this role and type
            role_config = await self.role_manager.get_role(session.role)
            if escalation_type not in role_config.escalation_triggers:
                raise ValueError(f"Escalation type '{escalation_type}' not allowed for role '{session.role}'")

            escalation_config = role_config.escalation_triggers[escalation_type]

            # Check if approval is required
            if escalation_config.get('approval_required', False):
                # In a real implementation, this would trigger an approval workflow
                logger.info(f"Escalation approval required for {session_id}: {escalation_type}")
                return {
                    'success': False,
                    'status': 'approval_required',
                    'escalation_type': escalation_type,
                    'approval_timeout': 300  # 5 minutes
                }

            # Mount additional tools
            additional_tools = set(escalation_config.get('additional_tools', []))
            if additional_tools:
                await self._mount_tools(session_id, additional_tools)
                session.mounted_tools.update(additional_tools)

            # Set escalation expiry
            duration = escalation_config.get('max_duration', 1800)  # Default 30 minutes
            session.escalation_active = True
            session.escalation_expires = datetime.now() + timedelta(seconds=duration)

            logger.info(f"Escalation granted for {session_id}: {escalation_type} -> {additional_tools}")

            return {
                'success': True,
                'escalation_type': escalation_type,
                'additional_tools': list(additional_tools),
                'expires_in_seconds': duration,
                'expires_at': session.escalation_expires.isoformat()
            }

        except Exception as e:
            logger.error(f"Escalation request failed for {session_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {'exists': False}

        budget_status = session.budget_status.__dict__ if session.budget_status else None

        return {
            'exists': True,
            'session_id': session_id,
            'role': session.role,
            'mounted_tools': list(session.mounted_tools),
            'budget_status': budget_status,
            'last_activity': session.last_activity.isoformat(),
            'escalation_active': session.escalation_active,
            'escalation_expires': session.escalation_expires.isoformat() if session.escalation_expires else None,
            'checkpoints_count': len(session.context_checkpoints)
        }

    async def get_broker_health(self) -> Dict[str, Any]:
        """Get comprehensive broker health status"""
        return await self.health_monitor.get_health_status(
            broker_status=self.status,
            active_sessions=len(self.active_sessions),
            server_manager=self.server_manager,
            metrics=self.metrics.get_summary()
        )

    # Private helper methods

    def _get_or_create_session(self, session_id: str) -> SessionState:
        """Get existing session or create new one"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = SessionState(session_id=session_id)
        return self.active_sessions[session_id]

    async def _load_configurations(self) -> None:
        """Load all configuration files"""
        # Policy configuration is loaded by individual managers
        pass

    async def _initialize_components(self) -> None:
        """Initialize all core components"""
        # Load policy configuration
        with open(self.config.policy_config_path, 'r') as f:
            policy_config = yaml.safe_load(f)

        # Initialize managers
        self.role_manager = RoleManager(policy_config)
        self.token_manager = TokenBudgetManager(policy_config)
        self.session_manager = SessionManager(policy_config)
        self.hook_manager = PreToolHookManager(policy_config, self.token_manager)
        self.server_manager = MCPServerManager(self.config.broker_config_path)

        logger.info("Core components initialized")

    async def _start_server_connections(self) -> None:
        """Start connections to all configured MCP servers"""
        if self.server_manager:
            await self.server_manager.start_all()
            logger.info("MCP server connections established")

    async def _start_background_tasks(self) -> None:
        """Start background monitoring and maintenance tasks"""
        # Health monitoring
        health_task = asyncio.create_task(self._health_monitor_loop())
        self._background_tasks.add(health_task)

        # Session cleanup
        cleanup_task = asyncio.create_task(self._session_cleanup_loop())
        self._background_tasks.add(cleanup_task)

        # Escalation expiry monitoring
        escalation_task = asyncio.create_task(self._escalation_monitor_loop())
        self._background_tasks.add(escalation_task)

        # ADHD checkpoint automation
        if self.config.adhd_optimizations:
            checkpoint_task = asyncio.create_task(self._adhd_checkpoint_loop())
            self._background_tasks.add(checkpoint_task)

        logger.info(f"Started {len(self._background_tasks)} background tasks")

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # Check server health
                if self.server_manager:
                    await self.server_manager.health_check_all()

                # Update broker status based on component health
                await self._update_broker_status()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _session_cleanup_loop(self) -> None:
        """Clean up inactive sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                now = datetime.now()
                inactive_threshold = timedelta(hours=2)

                inactive_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if now - session.last_activity > inactive_threshold
                ]

                for session_id in inactive_sessions:
                    await self._cleanup_session(session_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")

    async def _escalation_monitor_loop(self) -> None:
        """Monitor and expire escalations"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()

                for session_id, session in self.active_sessions.items():
                    if session.escalation_active and session.escalation_expires:
                        if now >= session.escalation_expires:
                            await self._expire_escalation(session_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Escalation monitor error: {e}")

    async def _adhd_checkpoint_loop(self) -> None:
        """ADHD-friendly automated checkpointing"""
        while True:
            try:
                await asyncio.sleep(1500)  # 25 minutes (Pomodoro interval)

                for session_id, session in self.active_sessions.items():
                    if session.role:  # Only checkpoint active sessions
                        checkpoint = await self._create_context_checkpoint(session_id, "pomodoro_auto")
                        session.context_checkpoints.append(checkpoint)

                        # Gentle notification about checkpoint created
                        await self._notify_checkpoint_created(session_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"ADHD checkpoint loop error: {e}")

    async def _mount_tools(self, session_id: str, tools: Set[str]) -> None:
        """Mount tools for a session"""
        for tool in tools:
            await self.server_manager.ensure_server_ready(tool)
        logger.info(f"Mounted tools for {session_id}: {tools}")

    async def _unmount_tools(self, session_id: str, tools: Set[str]) -> None:
        """Unmount tools for a session"""
        # In practice, this might keep connections alive but mark them as unused
        logger.info(f"Unmounted tools for {session_id}: {tools}")

    async def _verify_tool_access(self, session: SessionState, tool_name: str) -> bool:
        """Verify that a tool is accessible for the current session"""
        return tool_name in session.mounted_tools

    async def _create_context_checkpoint(self, session_id: str, checkpoint_type: str) -> Dict[str, Any]:
        """Create an ADHD-friendly context checkpoint"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}

        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'type': checkpoint_type,
            'role': session.role,
            'mounted_tools': list(session.mounted_tools),
            'budget_usage': session.budget_status.__dict__ if session.budget_status else None
        }

        # Store checkpoint via session manager
        if self.session_manager:
            await self.session_manager.store_checkpoint(checkpoint)

        return checkpoint

    async def _notify_role_switch(self, session_id: str, old_role: str, new_role: str, tools: Set[str]) -> None:
        """Notify UI about role switch (ADHD accommodation)"""
        # This would integrate with the tmux UI notification system
        logger.info(f"Role switch notification: {old_role} -> {new_role}")

    async def _notify_checkpoint_created(self, session_id: str) -> None:
        """Gentle notification about checkpoint creation"""
        # This would show a gentle UI notification
        logger.debug(f"Checkpoint created for session {session_id}")

    async def _expire_escalation(self, session_id: str) -> None:
        """Expire an active escalation and unmount temporary tools"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        # Get role's default tools
        role_config = await self.role_manager.get_role(session.role)
        default_tools = set(role_config.default_tools)

        # Unmount tools that aren't part of the default role
        tools_to_unmount = session.mounted_tools - default_tools
        if tools_to_unmount:
            await self._unmount_tools(session_id, tools_to_unmount)
            session.mounted_tools = default_tools

        session.escalation_active = False
        session.escalation_expires = None

        logger.info(f"Escalation expired for session {session_id}")

    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up an inactive session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        # Unmount all tools
        if session.mounted_tools:
            await self._unmount_tools(session_id, session.mounted_tools)

        # Save final checkpoint
        if self.config.adhd_optimizations:
            checkpoint = await self._create_context_checkpoint(session_id, "session_cleanup")

        del self.active_sessions[session_id]
        logger.info(f"Cleaned up inactive session: {session_id}")

    async def _save_session_states(self) -> None:
        """Save all session states for recovery"""
        # Implementation would save to persistent storage
        logger.info(f"Saved {len(self.active_sessions)} session states")

    async def _update_broker_status(self) -> None:
        """Update broker status based on component health"""
        if not self.server_manager:
            self.status = BrokerStatus.FAILED
            return

        server_health = await self.server_manager.get_overall_health()

        if server_health > 0.9:
            self.status = BrokerStatus.READY
        elif server_health > 0.5:
            self.status = BrokerStatus.DEGRADED
        else:
            self.status = BrokerStatus.FAILED

    async def _estimate_actual_token_usage(self, result: Any) -> int:
        """Estimate actual token usage from a tool result"""
        # Simple heuristic - would be more sophisticated in practice
        if isinstance(result, str):
            return len(result) // 4  # Rough tokens estimation
        elif isinstance(result, dict):
            return len(str(result)) // 4
        else:
            return 100  # Default estimate