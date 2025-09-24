"""
MCP Server Manager: Connection and lifecycle management for MCP servers

The MCP Server Manager handles the complex lifecycle management of multiple MCP
servers with different transport types (stdio, HTTP, WebSocket). It provides
centralized connection pooling, health monitoring, and graceful failover for
the MetaMCP role-aware tool brokering system.

Key Features:
- Multi-transport support (stdio, HTTP, WebSocket)
- Connection pooling and reuse for performance
- Health monitoring with automatic recovery
- Role-based server pre-warming
- Graceful startup/shutdown sequencing
- Circuit breaker pattern for failed connections

Integration Points:
- MetaMCP Broker: Primary consumer for tool call routing
- Health Monitor: Continuous health assessment
- Configuration: Dynamic server configuration loading
- Metrics: Performance and availability tracking
"""

import asyncio
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp
import websockets
import yaml

logger = logging.getLogger(__name__)


class ServerTransport(Enum):
    """Supported MCP server transport types"""

    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


class ServerStatus(Enum):
    """Server connection status"""

    UNKNOWN = "unknown"
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class ServerHealth:
    """Health status for a server"""

    status: ServerStatus
    last_check: datetime
    response_time_ms: float
    error_count: int = 0
    last_error: Optional[str] = None
    uptime_seconds: float = 0

    @property
    def is_healthy(self) -> bool:
        return self.status in [ServerStatus.READY, ServerStatus.DEGRADED]


@dataclass
class ServerConnection:
    """Active connection to an MCP server"""

    name: str
    transport: ServerTransport
    config: Dict[str, Any]
    process: Optional[subprocess.Popen] = None
    http_session: Optional[aiohttp.ClientSession] = None
    websocket: Optional[websockets.WebSocketServerProtocol] = None
    health: ServerHealth = field(
        default_factory=lambda: ServerHealth(
            status=ServerStatus.UNKNOWN, last_check=datetime.now(), response_time_ms=0.0
        )
    )
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        return (datetime.now() - self.last_used).total_seconds()


class MCPServerManager:
    """
    Manages lifecycle and connections for all MCP servers.

    The MCPServerManager provides centralized management of MCP server connections
    including startup/shutdown, health monitoring, connection pooling, and tool
    call routing. It supports multiple transport types and provides resilient
    connection management with automatic recovery.
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        # Active connections indexed by server name
        self.connections: Dict[str, ServerConnection] = {}

        # Connection pools for reuse
        self.connection_pools: Dict[str, List[ServerConnection]] = {}

        # Health monitoring
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None

        # Performance tracking
        self.call_counts: Dict[str, int] = {}
        self.response_times: Dict[str, List[float]] = {}

        # Circuit breaker state
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        logger.info("MCPServerManager initialized")

    async def start_all(self) -> None:
        """Start all configured MCP servers"""
        await self._load_configuration()

        # Start servers in dependency order
        startup_sequence = self._calculate_startup_sequence()

        for server_name in startup_sequence:
            try:
                await self._start_server(server_name)
                logger.info(f"Started MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Failed to start server {server_name}: {e}")
                # Continue with other servers

        # Start health monitoring
        await self._start_health_monitoring()

        logger.info(f"Started {len(self.connections)} MCP servers")

    async def stop_all(self) -> None:
        """Gracefully stop all MCP servers"""
        logger.info("Stopping all MCP servers...")

        # Stop health monitoring
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        # Stop servers in reverse order
        server_names = list(self.connections.keys())
        for server_name in reversed(server_names):
            try:
                await self._stop_server(server_name)
                logger.info(f"Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error stopping server {server_name}: {e}")

        logger.info("All MCP servers stopped")

    async def ensure_server_ready(self, server_name: str) -> bool:
        """Ensure a specific server is ready for use"""
        connection = self.connections.get(server_name)

        if not connection:
            # Try to start the server
            try:
                await self._start_server(server_name)
                connection = self.connections.get(server_name)
            except Exception as e:
                logger.error(f"Failed to start server {server_name}: {e}")
                return False

        if not connection:
            return False

        # Check if connection is healthy
        if connection.health.is_healthy:
            return True

        # Try to recover connection
        try:
            await self._recover_connection(server_name)
            return self.connections[server_name].health.is_healthy
        except Exception as e:
            logger.error(f"Failed to recover server {server_name}: {e}")
            return False

    async def call_tool(
        self, server_name: str, method: str, args: Dict[str, Any], timeout: int = 30
    ) -> Any:
        """Call a tool method on the specified MCP server"""
        start_time = time.time()

        try:
            # Ensure server is ready
            if not await self.ensure_server_ready(server_name):
                raise RuntimeError(f"Server {server_name} is not available")

            connection = self.connections[server_name]

            # Check circuit breaker
            if self._is_circuit_broken(server_name):
                raise RuntimeError(f"Circuit breaker open for server {server_name}")

            # Route call based on transport type
            if connection.transport == ServerTransport.STDIO:
                result = await self._call_stdio_tool(connection, method, args, timeout)
            elif connection.transport == ServerTransport.HTTP:
                result = await self._call_http_tool(connection, method, args, timeout)
            elif connection.transport == ServerTransport.WEBSOCKET:
                result = await self._call_websocket_tool(
                    connection, method, args, timeout
                )
            else:
                raise ValueError(f"Unsupported transport: {connection.transport}")

            # Update usage tracking
            connection.last_used = datetime.now()
            self.call_counts[server_name] = self.call_counts.get(server_name, 0) + 1

            # Record response time
            response_time = (time.time() - start_time) * 1000
            if server_name not in self.response_times:
                self.response_times[server_name] = []
            self.response_times[server_name].append(response_time)

            # Keep only recent response times (last 100 calls)
            if len(self.response_times[server_name]) > 100:
                self.response_times[server_name] = self.response_times[server_name][
                    -100:
                ]

            # Reset circuit breaker on success
            self._reset_circuit_breaker(server_name)

            return result

        except Exception as e:
            # Record failure for circuit breaker
            self._record_failure(server_name)
            raise e

    async def health_check_all(self) -> Dict[str, ServerHealth]:
        """Perform health check on all servers"""
        health_results = {}

        for server_name, connection in self.connections.items():
            try:
                health = await self._health_check_server(connection)
                connection.health = health
                health_results[server_name] = health
            except Exception as e:
                logger.error(f"Health check failed for {server_name}: {e}")
                connection.health.status = ServerStatus.FAILED
                connection.health.last_error = str(e)
                health_results[server_name] = connection.health

        return health_results

    async def get_overall_health(self) -> float:
        """Get overall health score (0.0 to 1.0)"""
        if not self.connections:
            return 0.0

        healthy_count = sum(
            1 for conn in self.connections.values() if conn.health.is_healthy
        )

        return healthy_count / len(self.connections)

    async def get_server_stats(self) -> Dict[str, Any]:
        """Get comprehensive server statistics"""
        stats = {
            "total_servers": len(self.connections),
            "healthy_servers": sum(
                1 for conn in self.connections.values() if conn.health.is_healthy
            ),
            "server_details": {},
            "transport_distribution": {},
            "overall_health": await self.get_overall_health(),
        }

        # Detailed server stats
        for name, connection in self.connections.items():
            response_times = self.response_times.get(name, [])
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            stats["server_details"][name] = {
                "status": connection.health.status.value,
                "transport": connection.transport.value,
                "uptime_seconds": connection.age_seconds,
                "last_used_seconds_ago": connection.idle_seconds,
                "call_count": self.call_counts.get(name, 0),
                "avg_response_time_ms": round(avg_response_time, 2),
                "error_count": connection.health.error_count,
                "last_error": connection.health.last_error,
            }

        # Transport distribution
        transport_counts = {}
        for connection in self.connections.values():
            transport = connection.transport.value
            transport_counts[transport] = transport_counts.get(transport, 0) + 1

        stats["transport_distribution"] = transport_counts

        return stats

    # Private helper methods

    async def _load_configuration(self) -> None:
        """Load server configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(
                f"Loaded server configuration: {len(self.config.get('servers', {}))} servers"
            )
        except Exception as e:
            logger.error(f"Failed to load server configuration: {e}")
            raise

    def _calculate_startup_sequence(self) -> List[str]:
        """Calculate optimal server startup sequence based on dependencies"""
        servers = self.config.get("servers", {})

        # For now, use a simple sequence based on startup timeout
        # In practice, this could analyze dependencies
        server_list = list(servers.keys())

        # Sort by startup timeout (faster servers first)
        server_list.sort(key=lambda name: servers[name].get("startup_timeout", 10))

        return server_list

    async def _start_server(self, server_name: str) -> None:
        """Start a specific MCP server"""
        server_config = self.config.get("servers", {}).get(server_name)
        if not server_config:
            raise ValueError(f"No configuration found for server: {server_name}")

        transport_str = server_config.get("transport", "stdio")
        transport = ServerTransport(transport_str)

        connection = ServerConnection(
            name=server_name, transport=transport, config=server_config
        )

        connection.health.status = ServerStatus.STARTING

        try:
            if transport == ServerTransport.STDIO:
                await self._start_stdio_server(connection)
            elif transport == ServerTransport.HTTP:
                await self._start_http_server(connection)
            elif transport == ServerTransport.WEBSOCKET:
                await self._start_websocket_server(connection)
            else:
                raise ValueError(f"Unsupported transport: {transport}")

            # Wait for server to be ready
            startup_timeout = server_config.get("startup_timeout", 10)
            await self._wait_for_server_ready(connection, startup_timeout)

            self.connections[server_name] = connection

            # Initialize circuit breaker
            self._init_circuit_breaker(server_name)

            logger.info(f"Successfully started {transport.value} server: {server_name}")

        except Exception as e:
            connection.health.status = ServerStatus.FAILED
            connection.health.last_error = str(e)
            raise e

    async def _start_stdio_server(self, connection: ServerConnection) -> None:
        """Start a stdio-based MCP server"""
        config = connection.config
        command = config.get("command", [])
        working_dir = config.get("working_directory", ".")
        env = config.get("environment", {})

        if not command:
            raise ValueError(
                f"No command specified for stdio server: {connection.name}"
            )

        try:
            # Prepare environment
            import os

            full_env = os.environ.copy()
            full_env.update(env)

            # Start process
            connection.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=full_env,
                text=True,
                bufsize=0,
            )

            logger.debug(
                f"Started stdio process for {connection.name}: PID {connection.process.pid}"
            )

        except Exception as e:
            logger.error(f"Failed to start stdio server {connection.name}: {e}")
            raise

    async def _start_http_server(self, connection: ServerConnection) -> None:
        """Start HTTP client session for HTTP-based MCP server"""
        config = connection.config
        url = config.get("url")

        if not url:
            raise ValueError(f"No URL specified for HTTP server: {connection.name}")

        # Create HTTP session with appropriate configuration
        timeout = aiohttp.ClientTimeout(total=30)

        # Set up authentication if needed
        headers = {}
        api_key_env = config.get("api_key_env")
        if api_key_env:
            import os

            api_key = os.getenv(api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        connection.http_session = aiohttp.ClientSession(
            timeout=timeout, headers=headers
        )

        logger.debug(f"Created HTTP session for {connection.name}")

    async def _start_websocket_server(self, connection: ServerConnection) -> None:
        """Start WebSocket connection for WebSocket-based MCP server"""
        config = connection.config
        url = config.get("url")

        if not url:
            raise ValueError(
                f"No URL specified for WebSocket server: {connection.name}"
            )

        try:
            connection.websocket = await websockets.connect(url)
            logger.debug(f"Connected to WebSocket server {connection.name}")
        except Exception as e:
            logger.error(
                f"Failed to connect to WebSocket server {connection.name}: {e}"
            )
            raise

    async def _wait_for_server_ready(
        self, connection: ServerConnection, timeout: int
    ) -> None:
        """Wait for server to become ready with timeout"""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            try:
                health = await self._health_check_server(connection)
                if health.status == ServerStatus.READY:
                    connection.health = health
                    return

                await asyncio.sleep(0.5)  # Check every 500ms

            except Exception:
                await asyncio.sleep(0.5)

        raise TimeoutError(
            f"Server {connection.name} did not become ready within {timeout}s"
        )

    async def _health_check_server(self, connection: ServerConnection) -> ServerHealth:
        """Perform health check on a specific server"""
        start_time = time.time()

        try:
            if connection.transport == ServerTransport.STDIO:
                success = await self._health_check_stdio(connection)
            elif connection.transport == ServerTransport.HTTP:
                success = await self._health_check_http(connection)
            elif connection.transport == ServerTransport.WEBSOCKET:
                success = await self._health_check_websocket(connection)
            else:
                success = False

            response_time = (time.time() - start_time) * 1000

            status = ServerStatus.READY if success else ServerStatus.FAILED

            health = ServerHealth(
                status=status,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_count=connection.health.error_count if not success else 0,
                uptime_seconds=connection.age_seconds,
            )

            if not success:
                health.error_count = connection.health.error_count + 1
                health.last_error = "Health check failed"

            return health

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return ServerHealth(
                status=ServerStatus.FAILED,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_count=connection.health.error_count + 1,
                last_error=str(e),
                uptime_seconds=connection.age_seconds,
            )

    async def _health_check_stdio(self, connection: ServerConnection) -> bool:
        """Health check for stdio server"""
        if not connection.process or connection.process.poll() is not None:
            return False

        # Simple ping by checking if process is still alive
        return True

    async def _health_check_http(self, connection: ServerConnection) -> bool:
        """Health check for HTTP server"""
        if not connection.http_session:
            return False

        config = connection.config
        health_config = config.get("health_check", {})
        endpoint = health_config.get("endpoint", "/health")

        try:
            url = config["url"].rstrip("/") + endpoint
            async with connection.http_session.get(
                url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def _health_check_websocket(self, connection: ServerConnection) -> bool:
        """Health check for WebSocket server"""
        if not connection.websocket:
            return False

        try:
            # Send a ping frame
            await connection.websocket.ping()
            return True
        except Exception:
            return False

    async def _call_stdio_tool(
        self,
        connection: ServerConnection,
        method: str,
        args: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Call tool method via stdio transport"""
        if not connection.process:
            raise RuntimeError(f"No stdio process for server {connection.name}")

        # Prepare JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": args,
        }

        request_json = json.dumps(request) + "\n"

        try:
            # Send request
            connection.process.stdin.write(request_json)
            connection.process.stdin.flush()

            # Read response with timeout
            response_line = await asyncio.wait_for(
                asyncio.create_task(self._read_stdio_line(connection.process)),
                timeout=timeout,
            )

            response = json.loads(response_line)

            if "error" in response:
                raise RuntimeError(f"Tool call error: {response['error']}")

            return response.get("result")

        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool call timeout after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"Tool call failed: {e}")

    async def _read_stdio_line(self, process: subprocess.Popen) -> str:
        """Read a line from stdio process asynchronously"""
        loop = asyncio.get_event_loop()

        def read_line():
            return process.stdout.readline()

        line = await loop.run_in_executor(None, read_line)
        return line.strip()

    async def _call_http_tool(
        self,
        connection: ServerConnection,
        method: str,
        args: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Call tool method via HTTP transport"""
        if not connection.http_session:
            raise RuntimeError(f"No HTTP session for server {connection.name}")

        # Prepare request
        url = connection.config["url"].rstrip("/") + "/tools/" + method

        try:
            async with connection.http_session.post(
                url, json=args, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:

                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"HTTP {response.status}: {error_text}")

                result = await response.json()
                return result

        except asyncio.TimeoutError:
            raise TimeoutError(f"HTTP tool call timeout after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"HTTP tool call failed: {e}")

    async def _call_websocket_tool(
        self,
        connection: ServerConnection,
        method: str,
        args: Dict[str, Any],
        timeout: int,
    ) -> Any:
        """Call tool method via WebSocket transport"""
        if not connection.websocket:
            raise RuntimeError(f"No WebSocket connection for server {connection.name}")

        # Prepare JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": args,
        }

        try:
            # Send request
            await connection.websocket.send(json.dumps(request))

            # Read response with timeout
            response_text = await asyncio.wait_for(
                connection.websocket.recv(), timeout=timeout
            )

            response = json.loads(response_text)

            if "error" in response:
                raise RuntimeError(f"WebSocket tool call error: {response['error']}")

            return response.get("result")

        except asyncio.TimeoutError:
            raise TimeoutError(f"WebSocket tool call timeout after {timeout}s")
        except Exception as e:
            raise RuntimeError(f"WebSocket tool call failed: {e}")

    async def _stop_server(self, server_name: str) -> None:
        """Stop a specific MCP server"""
        connection = self.connections.get(server_name)
        if not connection:
            return

        try:
            if connection.transport == ServerTransport.STDIO and connection.process:
                connection.process.terminate()
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(
                            self._wait_for_process_termination(connection.process)
                        ),
                        timeout=5,
                    )
                except asyncio.TimeoutError:
                    connection.process.kill()

            elif (
                connection.transport == ServerTransport.HTTP and connection.http_session
            ):
                await connection.http_session.close()

            elif (
                connection.transport == ServerTransport.WEBSOCKET
                and connection.websocket
            ):
                await connection.websocket.close()

            connection.health.status = ServerStatus.STOPPED

        except Exception as e:
            logger.error(f"Error stopping server {server_name}: {e}")

        finally:
            if server_name in self.connections:
                del self.connections[server_name]

    async def _wait_for_process_termination(self, process: subprocess.Popen) -> None:
        """Wait for process to terminate"""
        loop = asyncio.get_event_loop()

        def wait():
            process.wait()

        await loop.run_in_executor(None, wait)

    async def _recover_connection(self, server_name: str) -> None:
        """Attempt to recover a failed server connection"""
        logger.info(f"Attempting to recover server: {server_name}")

        # Stop current connection
        await self._stop_server(server_name)

        # Wait a bit before restart
        await asyncio.sleep(2)

        # Restart server
        await self._start_server(server_name)

        logger.info(f"Server recovery completed: {server_name}")

    async def _start_health_monitoring(self) -> None:
        """Start background health monitoring task"""

        async def health_monitor_loop():
            while True:
                try:
                    await asyncio.sleep(self.health_check_interval)
                    await self.health_check_all()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")

        self.health_check_task = asyncio.create_task(health_monitor_loop())
        logger.info("Started health monitoring")

    # Circuit breaker implementation

    def _init_circuit_breaker(self, server_name: str) -> None:
        """Initialize circuit breaker for a server"""
        self.circuit_breakers[server_name] = {
            "failure_count": 0,
            "last_failure": None,
            "state": "closed",  # closed, open, half_open
            "failure_threshold": 5,
            "recovery_timeout": 30,  # seconds
        }

    def _is_circuit_broken(self, server_name: str) -> bool:
        """Check if circuit breaker is open"""
        breaker = self.circuit_breakers.get(server_name, {})

        if breaker.get("state") == "open":
            # Check if we should try half-open
            last_failure = breaker.get("last_failure")
            if last_failure:
                time_since_failure = (datetime.now() - last_failure).total_seconds()
                if time_since_failure > breaker.get("recovery_timeout", 30):
                    breaker["state"] = "half_open"
                    return False
            return True

        return False

    def _record_failure(self, server_name: str) -> None:
        """Record a failure for circuit breaker logic"""
        if server_name not in self.circuit_breakers:
            self._init_circuit_breaker(server_name)

        breaker = self.circuit_breakers[server_name]
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.now()

        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for server {server_name}")

    def _reset_circuit_breaker(self, server_name: str) -> None:
        """Reset circuit breaker on successful operation"""
        if server_name in self.circuit_breakers:
            breaker = self.circuit_breakers[server_name]
            breaker["failure_count"] = 0
            breaker["state"] = "closed"
            breaker["last_failure"] = None
