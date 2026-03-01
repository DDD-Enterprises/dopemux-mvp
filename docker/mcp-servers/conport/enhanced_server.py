#!/usr/bin/env python3
"""
Enhanced ConPort Server - Real Database Persistence
Implements hybrid Redis + PostgreSQL backend for ADHD-optimized memory persistence
"""

import os
import asyncio
import sys
import logging
import signal
import json
import hashlib
from typing import Dict, Any, Optional, List
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the global error handling framework (Phase 2)
try:
    from dopemux.error_handling import (
        with_error_handling,
        create_dopemux_error,
        ErrorType,
        ErrorSeverity
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_AVAILABLE = False
    logger.warning("⚠️ Error handling framework not available")
    # Create dummy decorator
    def with_error_handling(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Worktree multi-instance support
try:
    from instance_detector import SimpleInstanceDetector
except ImportError:
    logger.warning("⚠️ Instance detector not available")
    SimpleInstanceDetector = None

# DopeconBridge event publishing
try:
    from integration_bridge_client import DopeconBridgeClient
except ImportError:
    logger.warning("⚠️ DopeconBridge client not available")
    DopeconBridgeClient = None

# Monitoring
sys.path.insert(0, '/app/shared')
try:
    from monitoring.base import DopemuxMonitoring
    from prometheus_client import make_asgi_app, generate_latest
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logger.warning("⚠️ Monitoring not available")

# Database and caching dependencies
try:
    from aiohttp import web, ClientSession
    import aiohttp
    import asyncpg
    import redis.asyncio as aioredis
    import uuid
except ImportError:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "aiohttp", "asyncpg", "redis"])
    from aiohttp import web, ClientSession
    import aiohttp
    import asyncpg
    import redis.asyncio as aioredis
    import uuid

class EnhancedConPortServer:
    """
    Enhanced ConPort server with real PostgreSQL + Redis persistence
    Optimized for ADHD context preservation and workflow continuity
    """

    def __init__(self):
        self.port = int(os.getenv('MCP_SERVER_PORT', 3004))
        self.host = '0.0.0.0'
        self.app = web.Application()

        # Database connections
        self.db_pool = None
        self.redis = None
        self.dopecon_bridge = None  # EventBus client for cross-service coordination
        self.unified_query_api = None  # F-NEW-7 Phase 2: Cross-workspace queries
        
        # Monitoring
        self.monitoring = None
        if MONITORING_AVAILABLE:
            self.monitoring = DopemuxMonitoring(
                service_name="conport",
                workspace_id=os.getenv("WORKSPACE_ID"),
                instance_id=os.getenv("INSTANCE_ID"),
                version=os.getenv("SERVICE_VERSION", "1.0.0")
            )
            logger.info("✅ Monitoring initialized")

        # Configuration
        self.postgres_url = os.getenv(
            'DATABASE_URL',
            'postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph'  # pragma: allowlist secret
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis-primary:6379')

        # ADHD-specific settings
        self.auto_save_interval = 30  # seconds
        self.context_cache_ttl = 300  # 5 minutes

        # Database optimization settings (Phase 3)
        self.query_cache_ttl = 180  # 3 minutes for query results
        self.connection_pool_min = int(os.getenv('DB_POOL_MIN', '5'))  # Increased for scalability
        self.connection_pool_max = int(os.getenv('DB_POOL_MAX', '20'))  # Higher for high load

        # Error handling framework integration (Phase 2)
        if ERROR_HANDLING_AVAILABLE:
            from dopemux.error_handling import GlobalErrorHandler, RetryPolicy
            self.error_handler = GlobalErrorHandler("conport-enhanced")

            # Register retry policy for database operations
            db_retry_policy = RetryPolicy(
                max_attempts=3,
                initial_delay=0.5,
                max_delay=5.0,
                backoff_factor=2.0,
                jitter=True
            )
            self.error_handler.register_retry_policy("api_retry", db_retry_policy)
        else:
            self.error_handler = None

        self.shutdown_event = asyncio.Event()
        self.auto_save_task = None
        self.auto_fork_progress = os.getenv('DOPEMUX_AUTO_FORK_PROGRESS', '1') == '1'

        # Setup monitoring middleware
        if MONITORING_AVAILABLE and self.monitoring:
            self.app.middlewares.append(self.monitoring_middleware)
        
        # Setup routes
        self.setup_routes()

    async def init_connections(self):
        """Initialize database and Redis connections"""
        try:
            # PostgreSQL connection pool (optimized for Phase 3 scalability)
            self.db_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=self.connection_pool_min,  # Configurable min connections
                max_size=self.connection_pool_max,  # Configurable max connections for high load
                max_queries=50000,  # Prevent connection exhaustion
                max_inactive_connection_lifetime=300,  # Recycle idle connections
                command_timeout=60,
                # Connection health checks
                server_settings={
                    'application_name': 'dopemux-conport-phase3',
                    'timezone': 'UTC'
                }
            )
            logger.info("✅ PostgreSQL connection pool established")

            # Ensure schema exists (one-time init)
            try:
                await self._ensure_schema()
            except Exception as se:
                logger.error(f"❌ Schema check/apply failed: {se}")
                raise

            # Redis connection
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis.ping()
            logger.info("✅ Redis connection established")

            # DopeconBridge client for event publishing
            if DopeconBridgeClient:
                self.dopecon_bridge = DopeconBridgeClient()
                await self.dopecon_bridge.initialize()
            else:
                self.dopecon_bridge = None
                logger.warning("⚠️ DopeconBridge not available")

            # F-NEW-7 Phase 2: Initialize unified query API
            try:
                from unified_queries import UnifiedQueryAPI
                self.unified_query_api = UnifiedQueryAPI(
                    db_pool=self.db_pool,
                    redis_client=self.redis,
                    schema='ag_catalog'
                )
                logger.info("✅ F-NEW-7 Unified Query API initialized")
            except ImportError:
                self.unified_query_api = None
                logger.warning("⚠️ Unified query API not available")

            # Start auto-save task for ADHD context preservation
            self.auto_save_task = asyncio.create_task(self.auto_save_loop())

        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise

    async def close_connections(self):
        """Cleanup database and Redis connections"""
        if self.auto_save_task:
            self.auto_save_task.cancel()

        if self.dopecon_bridge:
            await self.dopecon_bridge.close()

        if self.redis:
            await self.redis.close()

        if self.db_pool:
            await self.db_pool.close()

        logger.info("🔌 Connections closed")

    def setup_routes(self):
        """Setup HTTP API routes for ConPort access"""
        # Metrics endpoint
        if MONITORING_AVAILABLE:
            self.app.router.add_get('/metrics', self.metrics_handler)
        
        # Health check endpoint
        self.app.router.add_get('/health', self.health_check)

        # ConPort API endpoints
        self.app.router.add_get('/api/context/{workspace_id}', self.get_context)
        self.app.router.add_post('/api/context/{workspace_id}', self.update_context)

        # Decision logging endpoints
        self.app.router.add_post('/api/decisions', self.log_decision)
        self.app.router.add_get('/api/decisions', self.get_decisions)

        # Progress tracking endpoints
        self.app.router.add_post('/api/progress', self.log_progress)
        self.app.router.add_get('/api/progress', self.get_progress)
        self.app.router.add_put('/api/progress/{progress_id}', self.update_progress)

        # ADHD-specific endpoints
        self.app.router.add_get('/api/recent-activity/{workspace_id}', self.get_recent_activity)
        self.app.router.add_get('/api/active-work/{workspace_id}', self.get_active_work)

        # Search endpoints
        self.app.router.add_get('/api/search/{workspace_id}', self.search_content)

        # F-NEW-7 Phase 2: Unified query endpoints
        self.app.router.add_get('/api/unified-search', self.unified_search)
        self.app.router.add_get('/api/workspace-relationships', self.workspace_relationships)
        self.app.router.add_get('/api/workspace-summary', self.workspace_summary)

        # Custom data endpoints (generic key-value store)
        self.app.router.add_post('/api/custom_data', self.save_custom_data)
        self.app.router.add_get('/api/custom_data', self.get_custom_data)
        self.app.router.add_delete('/api/custom_data', self.delete_custom_data)

        # MCP compatibility endpoint
        self.app.router.add_post('/mcp', self.mcp_endpoint)

        # Instance management endpoints
        self.app.router.add_post('/api/instance/fork', self.fork_instance)
        self.app.router.add_post('/api/progress/promote', self.promote_progress)
        self.app.router.add_post('/api/progress/promote_all', self.promote_all)

    async def _fork_progress_from_shared(self, workspace_id: str, target_instance: Optional[str]) -> int:
        """Fork PLANNED/IN_PROGRESS progress from shared (instance_id NULL) to target instance."""
        if not target_instance:
            return 0
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM progress_entries
                 WHERE workspace_id = $1
                   AND (instance_id IS NULL OR instance_id = '')
                   AND status IN ('PLANNED','IN_PROGRESS')
                 ORDER BY created_at ASC
                """,
                workspace_id,
            )
            count = 0
            for r in rows:
                pid = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO progress_entries
                    (id, workspace_id, description, status, percentage,
                     linked_decision_id, priority, estimated_hours, actual_hours,
                     instance_id, created_at, updated_at)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,NOW(),NOW())
                    """,
                    pid,
                    r["workspace_id"],
                    r["description"],
                    r["status"],
                    r["percentage"],
                    r["linked_decision_id"],
                    r["priority"],
                    r["estimated_hours"],
                    r["actual_hours"],
                    target_instance,
                )
                count += 1
            return count

    @web.middleware
    async def monitoring_middleware(self, request, handler):
        """Track request metrics"""
        if not self.monitoring or request.path == '/metrics':
            return await handler(request)
        
        import time
        start_time = time.time()
        self.monitoring.requests_in_progress.labels(**self.monitoring.core_labels).inc()
        
        try:
            response = await handler(request)
            duration = time.time() - start_time
            
            # Record metrics
            self.monitoring.record_request(
                endpoint=request.path,
                method=request.method,
                status=response.status,
                duration=duration
            )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            self.monitoring.record_request(
                endpoint=request.path,
                method=request.method,
                status=500,
                duration=duration
            )
            self.monitoring.record_error("request_error", request.path)
            raise
        finally:
            self.monitoring.requests_in_progress.labels(**self.monitoring.core_labels).dec()

    @with_error_handling("health_check", retry_policy="api_retry")
    async def health_check(self, request):
        """Health check endpoint with connection status"""
        try:
            # Test database connection
            async with self.db_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            db_status = "healthy"

            # Test Redis connection
            await self.redis.ping()
            redis_status = "healthy"

            return web.json_response({
                'status': 'healthy',
                'service': 'conport-enhanced',
                'port': self.port,
                'database': db_status,
                'redis': redis_status,
                'timestamp': asyncio.get_event_loop().time()
            })
        except Exception as e:
            # Use DopemuxError for consistent error handling
            logger.error(f"Health check failed: {e}")
            from dopemux.error_handling import create_dopemux_error, ErrorType, ErrorSeverity
            error = create_dopemux_error(
                error_type=ErrorType.SERVICE_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
                message=f"ConPort health check failed: {e}",
                service_name="conport-enhanced",
                operation="health_check",
                details={"error": str(e)}
            )
            return web.json_response({
                'status': 'unhealthy',
                'error': error.to_dict(),
                'timestamp': asyncio.get_event_loop().time()
            }, status=503)

    async def metrics_handler(self, request):
        """Prometheus metrics endpoint"""
        if not MONITORING_AVAILABLE or not self.monitoring:
            return web.Response(text="Monitoring not available", status=404)
        
        metrics_output = generate_latest(self.monitoring.registry)
        return web.Response(
            body=metrics_output,
            content_type='text/plain; charset=utf-8'
        )

    async def _ensure_schema(self) -> None:
        """Ensure required tables exist; apply schema.sql via psql if missing."""
        async with self.db_pool.acquire() as conn:
            exists = await conn.fetchval(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'workspace_contexts'
                LIMIT 1
                """
            )
        if exists:
            logger.info("✅ Database schema present (workspace_contexts found)")
            return

        logger.info("🛠️  Database schema missing - applying /app/schema.sql")
        # Parse DATABASE_URL for psql connection params
        url = urlparse(self.postgres_url)
        user = url.username or ""
        password = url.password or ""
        host = url.hostname or "localhost"
        port = str(url.port or 5432)
        db = (url.path or "/").lstrip("/") or "postgres"

        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        # Apply schema using psql with ON_ERROR_STOP
        proc = await asyncio.create_subprocess_exec(
            "psql",
            "-h",
            host,
            "-p",
            port,
            "-U",
            user,
            "-d",
            db,
            "-v",
            "ON_ERROR_STOP=1",
            "-f",
            "/app/schema.sql",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode(errors="ignore") if stdout else ""
        if proc.returncode != 0:
            # Tolerate idempotent failures when objects already exist
            if "already exists" in output:
                logger.info("ℹ️  Schema already present; continuing")
            else:
                logger.error(f"❌ psql schema apply failed (exit {proc.returncode})\n{output}")
                raise RuntimeError("Schema apply failed")
        logger.info("✅ Applied schema.sql successfully")
        # Verify again
        async with self.db_pool.acquire() as conn:
            exists2 = await conn.fetchval(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'workspace_contexts'
                LIMIT 1
                """
            )
        if not exists2:
            logger.warning("⚠️  Schema verification query returned no rows; proceeding anyway")
            logger.info("✅ Schema verification OK")

        # Ensure optional columns for instance isolation exist
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("ALTER TABLE IF EXISTS progress_entries ADD COLUMN IF NOT EXISTS instance_id VARCHAR(255);")
                await conn.execute("ALTER TABLE IF EXISTS decisions ADD COLUMN IF NOT EXISTS instance_id VARCHAR(255);")
        except Exception as _e:
            logger.debug(f"Schema optional column ensure skipped: {_e}")

    async def get_context(self, request):
        """Get active context for workspace with worktree instance support"""
        workspace_id = request.match_info['workspace_id']

        try:
            # Worktree multi-instance: Get instance-specific context
            current_instance_id = SimpleInstanceDetector.get_instance_id()

            # Try Redis cache first (ADHD speed optimization)
            cache_key = f"context:{workspace_id}:{current_instance_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                logger.info(f"📋 Context cache hit for workspace: {workspace_id} (instance: {current_instance_id})")
                return web.json_response(json.loads(cached))

            # Check query result cache first (Phase 3 optimization)
            query_cache_key = f"query:context:{workspace_id}:{current_instance_id}"
            cached_query_result = await self.redis.get(query_cache_key)
            if cached_query_result:
                logger.debug(f"💾 Query cache hit for context: {workspace_id}")
                return web.json_response(json.loads(cached_query_result))

            # Fetch from database (instance-aware query)
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT workspace_id, instance_id, active_context, last_activity,
                           session_time, focus_state, session_milestone,
                           updated_at
                    FROM workspace_contexts
                    WHERE workspace_id = $1
                      AND (instance_id IS NULL AND $2::text IS NULL
                           OR instance_id = $2)
                """, workspace_id, current_instance_id)

                if row:
                    context = dict(row)
                    context['updated_at'] = context['updated_at'].isoformat()
                else:
                    # Seed from shared context if available; else create default
                    seed = await conn.fetchrow("""
                        SELECT workspace_id, null as instance_id, active_context, last_activity,
                               session_time, focus_state, session_milestone, updated_at
                          FROM workspace_contexts
                         WHERE workspace_id = $1 AND (instance_id IS NULL OR instance_id = '')
                         LIMIT 1
                    """, workspace_id)
                    if seed:
                        await conn.execute("""
                            INSERT INTO workspace_contexts
                            (workspace_id, instance_id, active_context, last_activity, session_time, focus_state, session_milestone)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, workspace_id, current_instance_id,
                            seed['active_context'], seed['last_activity'], seed['session_time'], seed['focus_state'], seed['session_milestone'])
                        context = dict(seed)
                        context['instance_id'] = current_instance_id
                    else:
                        context = {
                            'workspace_id': workspace_id,
                            'instance_id': current_instance_id,
                            'active_context': 'New ADHD-optimized session',
                            'last_activity': 'Session initialized',
                            'session_time': '0 minutes',
                            'focus_state': 'starting'
                        }
                        await conn.execute("""
                            INSERT INTO workspace_contexts
                            (workspace_id, instance_id, active_context, last_activity, session_time, focus_state)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, workspace_id, current_instance_id, context['active_context'], context['last_activity'],
                            context['session_time'], context['focus_state'])

            # Cache in Redis for fast access
            await self.redis.setex(cache_key, self.context_cache_ttl, json.dumps(context))

            # Cache query result for Phase 3 optimization
            await self.redis.setex(query_cache_key, self.query_cache_ttl, json.dumps(context))

            logger.info(f"📋 Retrieved context for workspace: {workspace_id}")
            return web.json_response(context)

        except Exception as e:
            logger.error(f"❌ Error getting context: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def update_context(self, request):
        """Update active context for workspace with worktree instance support"""
        workspace_id = request.match_info['workspace_id']
        data = await request.json()

        try:
            # Worktree multi-instance: Update instance-specific context
            current_instance_id = SimpleInstanceDetector.get_instance_id()

            async with self.db_pool.acquire() as conn:
                # Update database (instance-aware)
                await conn.execute("""
                    UPDATE workspace_contexts
                    SET active_context = COALESCE($2, active_context),
                        last_activity = COALESCE($3, last_activity),
                        session_time = COALESCE($4, session_time),
                        focus_state = COALESCE($5, focus_state),
                        session_milestone = COALESCE($6, session_milestone),
                        updated_at = NOW()
                    WHERE workspace_id = $1
                      AND (instance_id IS NULL AND $7::text IS NULL
                           OR instance_id = $7)
                """, workspace_id,
                    data.get('active_context'),
                    data.get('last_activity'),
                    data.get('session_time'),
                    data.get('focus_state'),
                    data.get('session_milestone'),
                    current_instance_id)

                # Get updated context
                row = await conn.fetchrow("""
                    SELECT workspace_id, instance_id, active_context, last_activity,
                           session_time, focus_state, session_milestone,
                           updated_at
                    FROM workspace_contexts
                    WHERE workspace_id = $1
                      AND (instance_id IS NULL AND $2::text IS NULL
                           OR instance_id = $2)
                """, workspace_id, current_instance_id)

                updated_context = dict(row)
                updated_context['updated_at'] = updated_context['updated_at'].isoformat()

            # Update Redis cache (instance-specific key)
            cache_key = f"context:{workspace_id}:{current_instance_id}"
            await self.redis.setex(cache_key, self.context_cache_ttl, json.dumps(updated_context))

            # Invalidate query result cache on updates (Phase 3 optimization)
            query_cache_key = f"query:context:{workspace_id}:{current_instance_id}"
            await self.redis.delete(query_cache_key)

            logger.info(f"📝 Updated context for workspace {workspace_id} (instance: {current_instance_id})")

            return web.json_response({
                'status': 'success',
                'workspace_id': workspace_id,
                'updated': updated_context
            })

        except Exception as e:
            logger.error(f"❌ Error updating context: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def log_decision(self, request):
        """Log a decision with rationale to database"""
        data = await request.json()

        try:
            decision_id = str(uuid.uuid4())

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO decisions
                    (id, workspace_id, summary, rationale, alternatives, tags,
                     confidence_level, decision_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, decision_id,
                    data.get('workspace_id'),
                    data.get('summary'),
                    data.get('rationale'),
                    json.dumps(data.get('alternatives', [])),
                    data.get('tags', []),
                    data.get('confidence_level', 'medium'),
                    data.get('decision_type', 'implementation'))

                # Get the inserted decision
                row = await conn.fetchrow("""
                    SELECT * FROM decisions WHERE id = $1
                """, decision_id)

                decision_entry = dict(row)
                decision_entry['id'] = str(decision_entry['id'])  # Convert UUID to string
                decision_entry['created_at'] = decision_entry['created_at'].isoformat()
                decision_entry['updated_at'] = decision_entry['updated_at'].isoformat()
                decision_entry['alternatives'] = json.loads(decision_entry['alternatives'])

            # Invalidate related caches
            workspace_id = data.get('workspace_id')
            if workspace_id:
                await self.redis.delete(f"decisions:{workspace_id}")
                await self.redis.delete(f"recent_activity:{workspace_id}")

            # Publish decision_logged event to DopeconBridge
            if self.dopecon_bridge:
                current_instance_id = SimpleInstanceDetector.get_instance_id()
                await self.dopecon_bridge.publish_decision_logged(
                    decision_id=decision_id,
                    summary=data.get('summary'),
                    workspace_id=workspace_id,
                    tags=data.get('tags', []),
                    extra={"instance_id": current_instance_id}
                )

            logger.info(f"💡 Logged decision: {data.get('summary')}")

            return web.json_response({
                'status': 'logged',
                'decision': decision_entry
            })

        except Exception as e:
            logger.error(f"❌ Error logging decision: {e}")
            return web.json_response({'error': str(e)}, status=500)

    def _estimate_tokens(self, text: str) -> int:
        """Conservative token estimation: 1 token ≈ 4 chars."""
        if text is None:
            return 0
        return len(str(text)) // 4

    def _truncate_decisions(self, decisions: list, max_tokens: int = 9000) -> tuple[list, dict]:
        """
        Truncate decision list to fit token budget.

        Returns (truncated_decisions, stats_dict)
        """
        result = []
        estimated_tokens = 200  # Base overhead for JSON structure

        for decision in decisions:
            # Estimate tokens for this decision
            decision_json = str(decision)  # Rough estimate via string conversion
            item_tokens = self._estimate_tokens(decision_json)

            if estimated_tokens + item_tokens > max_tokens:
                # Would exceed budget, stop here
                break

            result.append(decision)
            estimated_tokens += item_tokens

        stats = {
            'original_count': len(decisions),
            'returned_count': len(result),
            'estimated_tokens': estimated_tokens,
            'truncated': len(result) < len(decisions)
        }

        return result, stats

    def _truncate_progress(self, items: list, max_tokens: int = 9000) -> tuple[list, dict]:
        """
        Truncate progress entries to fit token budget.

        Returns (truncated_items, stats_dict)
        """
        result = []
        estimated_tokens = 200  # Base overhead

        for item in items:
            item_json = str(item)
            item_tokens = self._estimate_tokens(item_json)

            if estimated_tokens + item_tokens > max_tokens:
                break

            result.append(item)
            estimated_tokens += item_tokens

        stats = {
            'original_count': len(items),
            'returned_count': len(result),
            'estimated_tokens': estimated_tokens,
            'truncated': len(result) < len(items)
        }

        return result, stats

    async def get_decisions(self, request):
        """Get decision history for a workspace (or all if not specified) with caching."""
        workspace_id = request.query.get('workspace_id')
        limit = int(request.query.get('limit', 10))

        try:
            # Check query result cache (Phase 3 optimization)
            cache_key = f"query:decisions:{workspace_id or 'all'}:{limit}"
            cached_result = await self.redis.get(cache_key)
            if cached_result:
                logger.debug(f"💾 Query cache hit for decisions: {workspace_id or 'all'}")
                return web.json_response(json.loads(cached_result))
            cache_key = f"decisions:{workspace_id or 'ALL'}:{limit}"
            cached = await self.redis.get(cache_key)
            if cached:
                return web.json_response(json.loads(cached))

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, workspace_id, summary, rationale, alternatives,
                           tags, confidence_level, decision_type, created_at
                    FROM decisions
                    WHERE ($1::text IS NULL OR workspace_id = $1)
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    workspace_id,
                    limit,
                )

            decisions = []
            for row in rows:
                d = dict(row)
                d['id'] = str(d['id'])
                d['created_at'] = d['created_at'].isoformat()
                d['alternatives'] = json.loads(d['alternatives'])
                decisions.append(d)

            decisions, trunc_stats = self._truncate_decisions(decisions, max_tokens=9000)

            result = {
                'workspace_id': workspace_id,
                'decisions': decisions,
                'count': len(decisions),
                'truncation_stats': trunc_stats if trunc_stats.get('truncated') else None,
            }

            await self.redis.setex(cache_key, 300, json.dumps(result))

            # Cache query result for Phase 3 optimization
            await self.redis.setex(f"query:decisions:{workspace_id or 'all'}:{limit}", self.query_cache_ttl, json.dumps(result))

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting decisions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_progress(self, request):
        """Get progress entries for a workspace, optionally filtered by status."""
        workspace_id = request.query.get('workspace_id')
        status = request.query.get('status')  # e.g., IN_PROGRESS, COMPLETED
        limit = int(request.query.get('limit', 20))

        try:
            cache_key = f"progress:{workspace_id or 'ALL'}:{status or 'ALL'}:{limit}"
            cached = await self.redis.get(cache_key)
            if cached:
                return web.json_response(json.loads(cached))

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, workspace_id, description, status, percentage,
                           linked_decision_id, priority, estimated_hours, actual_hours,
                           created_at, updated_at, completed_at
                    FROM progress_entries
                    WHERE ($1::text IS NULL OR workspace_id = $1)
                      AND ($2::text IS NULL OR status = $2)
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    workspace_id,
                    status,
                    limit,
                )

            items = []
            for row in rows:
                p = dict(row)
                p['id'] = str(p['id'])
                if p.get('linked_decision_id'):
                    p['linked_decision_id'] = str(p['linked_decision_id'])
                p['created_at'] = p['created_at'].isoformat()
                p['updated_at'] = p['updated_at'].isoformat()
                if p.get('completed_at'):
                    p['completed_at'] = p['completed_at'].isoformat()
                items.append(p)

            # Auto-fork from shared if empty and enabled
            if not items and self.auto_fork_progress and workspace_id:
                current_instance_id = SimpleInstanceDetector.get_instance_id()
                try:
                    forked = await self._fork_progress_from_shared(workspace_id, current_instance_id)
                    if forked:
                        rows = await self.db_pool.fetch(
                            """
                            SELECT id, workspace_id, description, status, percentage,
                                   linked_decision_id, priority, estimated_hours, actual_hours,
                                   created_at, updated_at, completed_at
                              FROM progress_entries
                             WHERE ($1::text IS NULL OR workspace_id = $1)
                               AND ($2::text IS NULL OR status = $2)
                               AND ($4::text IS NULL OR instance_id = $4)
                             ORDER BY created_at DESC
                             LIMIT $3
                            """,
                            workspace_id,
                            status,
                            limit,
                            current_instance_id,
                        )
                        for row in rows:
                            p = dict(row)
                            p['id'] = str(p['id'])
                            if p.get('linked_decision_id'):
                                p['linked_decision_id'] = str(p['linked_decision_id'])
                            p['created_at'] = p['created_at'].isoformat()
                            p['updated_at'] = p['updated_at'].isoformat()
                            if p.get('completed_at'):
                                p['completed_at'] = p['completed_at'].isoformat()
                            items.append(p)
                except Exception as _e:
                    pass

            items, trunc_stats = self._truncate_progress(items, max_tokens=9000)

            result = {
                'workspace_id': workspace_id,
                'progress': items,
                'count': len(items),
                'truncation_stats': trunc_stats if trunc_stats.get('truncated') else None,
            }

            await self.redis.setex(cache_key, 300, json.dumps(result))
            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting progress: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def fork_instance(self, request):
        """Fork active progress from a source instance to target (current) instance."""
        data = await request.json()
        workspace_id = data.get('workspace_id')
        source_instance = data.get('source_instance')  # None or '' means shared
        target_instance = data.get('target_instance') or SimpleInstanceDetector.get_instance_id()
        if not workspace_id:
            return web.json_response({'error': 'workspace_id required'}, status=400)
        if not target_instance:
            return web.json_response({'error': 'target_instance not detected'}, status=400)
        try:
            count = 0
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM progress_entries
                     WHERE workspace_id = $1
                       AND ($2::text IS NULL OR instance_id = $2)
                       AND (($2::text IS NULL AND (instance_id IS NULL OR instance_id = '')) OR $2::text IS NOT NULL)
                       AND status IN ('PLANNED','IN_PROGRESS')
                    """,
                    workspace_id,
                    source_instance,
                )
                for r in rows:
                    pid = str(uuid.uuid4())
                    await conn.execute(
                        """
                        INSERT INTO progress_entries
                        (id, workspace_id, description, status, percentage,
                         linked_decision_id, priority, estimated_hours, actual_hours,
                         instance_id, created_at, updated_at)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,NOW(),NOW())
                        """,
                        pid,
                        r['workspace_id'],
                        r['description'],
                        r['status'],
                        r['percentage'],
                        r['linked_decision_id'],
                        r['priority'],
                        r['estimated_hours'],
                        r['actual_hours'],
                        target_instance,
                    )
                    count += 1
            return web.json_response({'status': 'forked', 'workspace_id': workspace_id, 'source_instance': source_instance, 'target_instance': target_instance, 'count': count})
        except Exception as e:
            logger.error(f"❌ Fork instance failed: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def promote_progress(self, request):
        """Promote an instance-local progress entry to shared (instance_id=NULL)."""
        data = await request.json()
        progress_id = data.get('progress_id')
        if not progress_id:
            return web.json_response({'error': 'progress_id required'}, status=400)
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM progress_entries WHERE id = $1", progress_id)
                if not row:
                    return web.json_response({'error': 'not found'}, status=404)
                await conn.execute(
                    """
                    UPDATE progress_entries
                       SET instance_id = NULL,
                           updated_at = NOW()
                     WHERE id = $1
                    """,
                    progress_id,
                )

            # Publish event for DDG
            if self.dopecon_bridge:
                await self.dopecon_bridge.publish_progress_updated(
                    progress_id=progress_id,
                    status=row['status'],
                    description=row['description'],
                    workspace_id=row['workspace_id'],
                    percentage=row.get('percentage', 0),
                    extra={"instance_id": None},
                )

            return web.json_response({'status': 'promoted', 'progress_id': progress_id})
        except Exception as e:
            logger.error(f"❌ Promote progress failed: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def promote_all(self, request):
        """Promote all instance-local PLANNED/IN_PROGRESS entries to shared for a workspace."""
        data = await request.json()
        workspace_id = data.get('workspace_id')
        if not workspace_id:
            return web.json_response({'error': 'workspace_id required'}, status=400)
        try:
            current_instance_id = SimpleInstanceDetector.get_instance_id()
            if not current_instance_id:
                return web.json_response({'error': 'No current instance detected'}, status=400)
            count = 0
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, status, description
                      FROM progress_entries
                     WHERE workspace_id = $1
                       AND instance_id = $2
                       AND status IN ('PLANNED','IN_PROGRESS')
                    """,
                    workspace_id,
                    current_instance_id,
                )
                for r in rows:
                    await conn.execute(
                        "UPDATE progress_entries SET instance_id = NULL, updated_at = NOW() WHERE id = $1",
                        r['id'],
                    )
                    count += 1
                    if self.dopecon_bridge:
                        await self.dopecon_bridge.publish_progress_updated(
                            progress_id=str(r['id']),
                            status=r['status'],
                            description=r['description'],
                            workspace_id=workspace_id,
                            percentage=0,
                            extra={"instance_id": None},
                        )
            return web.json_response({'status': 'promoted_all', 'workspace_id': workspace_id, 'instance_id': current_instance_id, 'count': count})
        except Exception as e:
            logger.error(f"❌ Promote all failed: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def log_progress(self, request):
        """Create a new progress entry."""
        data = await request.json()

        try:
            pid = str(uuid.uuid4())
            workspace_id = data.get('workspace_id')
            description = data.get('description')
            if not workspace_id or not description:
                return web.json_response({'error': 'workspace_id and description are required'}, status=400)

            status = data.get('status', 'IN_PROGRESS')
            percentage = int(data.get('percentage', 0))
            linked_decision_id = data.get('linked_decision_id')
            priority = data.get('priority', 'medium')
            estimated_hours = data.get('estimated_hours')
            actual_hours = data.get('actual_hours')

            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO progress_entries
                    (id, workspace_id, description, status, percentage,
                     linked_decision_id, priority, estimated_hours, actual_hours)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    pid,
                    workspace_id,
                    description,
                    status,
                    percentage,
                    linked_decision_id,
                    priority,
                    estimated_hours,
                    actual_hours,
                )

                row = await conn.fetchrow("SELECT * FROM progress_entries WHERE id = $1", pid)

            entry = dict(row)
            entry['id'] = str(entry['id'])
            if entry.get('linked_decision_id'):
                entry['linked_decision_id'] = str(entry['linked_decision_id'])
            entry['created_at'] = entry['created_at'].isoformat()
            entry['updated_at'] = entry['updated_at'].isoformat()
            if entry.get('completed_at'):
                entry['completed_at'] = entry['completed_at'].isoformat()

            # Invalidate caches
            await self.redis.delete(f"progress:{workspace_id}")
            await self.redis.delete(f"active_work:{workspace_id}")
            await self.redis.delete(f"recent_activity:{workspace_id}")

            # Publish event (best-effort)
            if self.dopecon_bridge:
                await self.dopecon_bridge.publish_progress_updated(
                    progress_id=pid,
                    status=entry['status'],
                    description=entry['description'],
                    workspace_id=workspace_id,
                    percentage=entry.get('percentage', 0),
                )

            logger.info(f"🆕 Progress logged: {description} [{status}]")

            return web.json_response({'status': 'logged', 'progress': entry})

        except Exception as e:
            logger.error(f"❌ Error logging progress: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def update_progress(self, request):
        """Update existing progress entry with worktree instance transition handling"""
        progress_id = request.match_info['progress_id']
        data = await request.json()

        try:
            new_status = data.get('status')

            # Worktree multi-instance: Handle status transitions
            # When transitioning TO shared status (COMPLETED/BLOCKED):
            #   → Clear instance_id (make visible to all worktrees)
            # When transitioning TO isolated status (IN_PROGRESS/PLANNED):
            #   → Set instance_id (make visible only in this worktree)
            if new_status:
                current_instance_id = SimpleInstanceDetector.get_instance_id()

                if SimpleInstanceDetector.is_isolated_status(new_status):
                    # Transitioning to isolated status
                    final_instance_id = current_instance_id
                else:
                    # Transitioning to shared status
                    final_instance_id = None

                # Update with instance_id transition
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE progress_entries
                        SET status = $2,
                            instance_id = $3,
                            percentage = COALESCE($4, percentage),
                            description = COALESCE($5, description),
                            priority = COALESCE($6, priority),
                            actual_hours = COALESCE($7, actual_hours),
                            updated_at = NOW()
                        WHERE id = $1
                    """, progress_id,
                        new_status,
                        final_instance_id,
                        data.get('percentage'),
                        data.get('description'),
                        data.get('priority'),
                        data.get('actual_hours'))
            else:
                # No status change - update other fields only
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE progress_entries
                        SET percentage = COALESCE($2, percentage),
                            description = COALESCE($3, description),
                            priority = COALESCE($4, priority),
                            actual_hours = COALESCE($5, actual_hours),
                            updated_at = NOW()
                        WHERE id = $1
                    """, progress_id,
                        data.get('percentage'),
                        data.get('description'),
                        data.get('priority'),
                        data.get('actual_hours'))

                # Get updated progress entry
                row = await conn.fetchrow("""
                    SELECT * FROM progress_entries WHERE id = $1
                """, progress_id)

                if not row:
                    return web.json_response({'error': 'Progress entry not found'}, status=404)

                progress_entry = dict(row)
                progress_entry['id'] = str(progress_entry['id'])  # Convert UUID to string
                if progress_entry['linked_decision_id']:
                    progress_entry['linked_decision_id'] = str(progress_entry['linked_decision_id'])
                progress_entry['created_at'] = progress_entry['created_at'].isoformat()
                progress_entry['updated_at'] = progress_entry['updated_at'].isoformat()
                if progress_entry['completed_at']:
                    progress_entry['completed_at'] = progress_entry['completed_at'].isoformat()

            # Invalidate caches
            workspace_id = progress_entry.get('workspace_id')
            if workspace_id:
                await self.redis.delete(f"progress:{workspace_id}")
                await self.redis.delete(f"active_work:{workspace_id}")

            # Publish progress_updated event to DopeconBridge
            if self.dopecon_bridge:
                current_instance_id = SimpleInstanceDetector.get_instance_id()
                await self.dopecon_bridge.publish_progress_updated(
                    progress_id=progress_id,
                    status=progress_entry['status'],
                    description=progress_entry['description'],
                    workspace_id=workspace_id,
                    percentage=progress_entry.get('percentage', 0),
                    extra={"instance_id": current_instance_id}
                )

            logger.info(f"📊 Progress updated: {progress_entry['description']} → {progress_entry['status']}")

            return web.json_response({
                'status': 'updated',
                'progress': progress_entry
            })

        except Exception as e:
            logger.error(f"❌ Error updating progress: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_recent_activity(self, request):
        """Get recent activity for ADHD context awareness"""
        workspace_id = request.match_info['workspace_id']
        hours = int(request.query.get('hours', 24))

        try:
            cache_key = f"recent_activity:{workspace_id}:{hours}"
            cached = await self.redis.get(cache_key)

            if cached:
                return web.json_response(json.loads(cached))

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM recent_activity
                    WHERE workspace_id = $1
                      AND created_at > NOW() - INTERVAL '%s hours'
                    ORDER BY created_at DESC
                    LIMIT 20
                """ % hours, workspace_id)

                activities = []
                for row in rows:
                    activity = dict(row)
                    activity['created_at'] = activity['created_at'].isoformat()
                    activities.append(activity)

            result = {
                'workspace_id': workspace_id,
                'activities': activities,
                'hours_back': hours
            }

            await self.redis.setex(cache_key, 180, json.dumps(result))  # 3 min cache

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting recent activity: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_active_work(self, request):
        """Get active work items for ADHD focus"""
        workspace_id = request.match_info['workspace_id']

        try:
            cache_key = f"active_work:{workspace_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                return web.json_response(json.loads(cached))

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM active_work
                    WHERE workspace_id = $1
                    ORDER BY
                        CASE priority
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at
                """, workspace_id)

                active_items = []
                for row in rows:
                    item = dict(row)
                    item['created_at'] = item['created_at'].isoformat()
                    active_items.append(item)

            result = {
                'workspace_id': workspace_id,
                'active_work': active_items,
                'count': len(active_items)
            }

            await self.redis.setex(cache_key, 180, json.dumps(result))

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting active work: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def search_content(self, request):
        """Search decisions and progress entries"""
        workspace_id = request.match_info['workspace_id']
        query = request.query.get('q', '')
        search_type = request.query.get('type', 'all')  # 'decisions', 'progress', 'all'

        if not query:
            return web.json_response({'error': 'Query parameter q is required'}, status=400)

        try:
            # Create cache key
            query_hash = hashlib.md5(f"{workspace_id}:{query}:{search_type}".encode()).hexdigest()
            cache_key = f"search:{query_hash}"
            cached = await self.redis.get(cache_key)

            if cached:
                return web.json_response(json.loads(cached))

            results = {'decisions': [], 'progress': []}

            async with self.db_pool.acquire() as conn:
                if search_type in ['decisions', 'all']:
                    decision_rows = await conn.fetch("""
                        SELECT id, workspace_id, summary, rationale, created_at,
                               ts_rank(to_tsvector('english', summary || ' ' || rationale),
                                      plainto_tsquery('english', $2)) as rank
                        FROM decisions
                        WHERE workspace_id = $1
                          AND to_tsvector('english', summary || ' ' || rationale) @@
                              plainto_tsquery('english', $2)
                        ORDER BY rank DESC, created_at DESC
                        LIMIT 10
                    """, workspace_id, query)

                    for row in decision_rows:
                        decision = dict(row)
                        decision['created_at'] = decision['created_at'].isoformat()
                        results['decisions'].append(decision)

                if search_type in ['progress', 'all']:
                    progress_rows = await conn.fetch("""
                        SELECT id, workspace_id, description, status, percentage, created_at
                        FROM progress_entries
                        WHERE workspace_id = $1
                          AND (description ILIKE $2 OR status ILIKE $2)
                        ORDER BY created_at DESC
                        LIMIT 10
                    """, workspace_id, f'%{query}%')

                    for row in progress_rows:
                        progress = dict(row)
                        progress['created_at'] = progress['created_at'].isoformat()
                        results['progress'].append(progress)

            result = {
                'workspace_id': workspace_id,
                'query': query,
                'results': results,
                'total_count': len(results['decisions']) + len(results['progress'])
            }

            await self.redis.setex(cache_key, 300, json.dumps(result))

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error searching content: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def auto_save_loop(self):
        """ADHD-optimized auto-save loop for context preservation"""
        logger.info(f"🔄 Auto-save loop started (every {self.auto_save_interval}s)")

        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.auto_save_interval)

                if self.shutdown_event.is_set():
                    break

                # Auto-save all active contexts (ADHD context preservation)
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE workspace_contexts
                        SET updated_at = NOW()
                        WHERE updated_at > NOW() - INTERVAL '5 minutes'
                    """)

                logger.debug("💾 Auto-save completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Auto-save error: {e}")

    async def save_custom_data(self, request):
        """Save or update custom data in key-value store"""
        try:
            data = await request.json()
            workspace_id = data.get('workspace_id')
            category = data.get('category')
            key = data.get('key')
            value = data.get('value')

            if not all([workspace_id, category, key, value is not None]):
                return web.json_response({
                    'error': 'Missing required fields: workspace_id, category, key, value'
                }, status=400)

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO custom_data (workspace_id, category, key, value, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (workspace_id, category, key)
                    DO UPDATE SET value = $4, updated_at = NOW()
                """, workspace_id, category, key, json.dumps(value))

            # Invalidate cache
            cache_key = f"custom_data:{workspace_id}:{category}:{key}"
            await self.redis.delete(cache_key)

            logger.info(f"💾 Custom data saved: {category}/{key}")

            return web.json_response({
                'status': 'saved',
                'workspace_id': workspace_id,
                'category': category,
                'key': key
            })

        except Exception as e:
            logger.error(f"Error saving custom data: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_custom_data(self, request):
        """Retrieve custom data from key-value store"""
        try:
            workspace_id = request.query.get('workspace_id')
            category = request.query.get('category')
            key = request.query.get('key')

            if not workspace_id:
                return web.json_response({
                    'error': 'Missing required parameter: workspace_id'
                }, status=400)

            async with self.db_pool.acquire() as conn:
                if category and key:
                    # Get specific item
                    row = await conn.fetchrow("""
                        SELECT category, key, value, created_at, updated_at
                        FROM custom_data
                        WHERE workspace_id = $1 AND category = $2 AND key = $3
                    """, workspace_id, category, key)

                    if not row:
                        return web.json_response({
                            'error': 'Not found'
                        }, status=404)

                    result = dict(row)
                    result['value'] = json.loads(result['value']) if isinstance(result['value'], str) else result['value']
                    result['created_at'] = result['created_at'].isoformat()
                    result['updated_at'] = result['updated_at'].isoformat()

                    return web.json_response(result)

                elif category:
                    # Get all items in category
                    rows = await conn.fetch("""
                        SELECT category, key, value, created_at, updated_at
                        FROM custom_data
                        WHERE workspace_id = $1 AND category = $2
                        ORDER BY key
                    """, workspace_id, category)

                    items = []
                    for row in rows:
                        item = dict(row)
                        item['value'] = json.loads(item['value']) if isinstance(item['value'], str) else item['value']
                        item['created_at'] = item['created_at'].isoformat()
                        item['updated_at'] = item['updated_at'].isoformat()
                        items.append(item)

                    return web.json_response({
                        'workspace_id': workspace_id,
                        'category': category,
                        'items': items,
                        'count': len(items)
                    })

                else:
                    # Get all categories
                    rows = await conn.fetch("""
                        SELECT category, key, value, created_at, updated_at
                        FROM custom_data
                        WHERE workspace_id = $1
                        ORDER BY category, key
                    """, workspace_id)

                    items = []
                    for row in rows:
                        item = dict(row)
                        item['value'] = json.loads(item['value']) if isinstance(item['value'], str) else item['value']
                        item['created_at'] = item['created_at'].isoformat()
                        item['updated_at'] = item['updated_at'].isoformat()
                        items.append(item)

                    return web.json_response({
                        'workspace_id': workspace_id,
                        'items': items,
                        'count': len(items)
                    })

        except Exception as e:
            logger.error(f"Error retrieving custom data: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def delete_custom_data(self, request):
        """Delete custom data from key-value store"""
        try:
            workspace_id = request.query.get('workspace_id')
            category = request.query.get('category')
            key = request.query.get('key')

            if not all([workspace_id, category, key]):
                return web.json_response({
                    'error': 'Missing required parameters: workspace_id, category, key'
                }, status=400)

            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM custom_data
                    WHERE workspace_id = $1 AND category = $2 AND key = $3
                """, workspace_id, category, key)

            # Invalidate cache
            cache_key = f"custom_data:{workspace_id}:{category}:{key}"
            await self.redis.delete(cache_key)

            logger.info(f"🗑️  Custom data deleted: {category}/{key}")

            return web.json_response({
                'status': 'deleted',
                'workspace_id': workspace_id,
                'category': category,
                'key': key
            })

        except Exception as e:
            logger.error(f"Error deleting custom data: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def mcp_endpoint(self, request):
        """MCP compatibility endpoint for future integration"""
        try:
            mcp_request = await request.json()

            response = {
                'jsonrpc': '2.0',
                'id': mcp_request.get('id'),
                'result': {
                    'status': 'enhanced_persistence_active',
                    'message': 'ConPort enhanced server with PostgreSQL + Redis persistence',
                    'features': ['context_persistence', 'decision_tracking', 'progress_monitoring', 'adhd_optimization']
                }
            }

            return web.json_response(response)

        except Exception as e:
            logger.error(f"MCP endpoint error: {e}")
            return web.json_response({
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }, status=500)

    # =====================================================================
    # F-NEW-7 Phase 2: Unified Query Endpoints
    # =====================================================================

    async def unified_search(self, request):
        """
        Cross-workspace full-text search endpoint.

        Query params:
            user_id: User identifier (required)
            query: Search query (required)
            workspaces: Comma-separated workspace IDs (optional, defaults to all)
            limit: Max results (optional, default 50)

        Returns:
            List of search results with relevance scores

        Performance: <200ms target (ADHD requirement)
        """
        try:
            user_id = request.query.get('user_id')
            query = request.query.get('query')

            if not user_id or not query:
                return web.json_response(
                    {'error': 'user_id and query are required'},
                    status=400
                )

            # Parse workspaces
            workspaces_str = request.query.get('workspaces')
            workspaces = workspaces_str.split(',') if workspaces_str else None

            limit = int(request.query.get('limit', 50))

            # Execute unified search
            start_time = datetime.now()
            results = await self.unified_query_api.search_across_workspaces(
                user_id=user_id,
                query=query,
                workspaces=workspaces,
                limit=limit
            )
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Convert results to JSON-serializable format
            results_json = [
                {
                    'decision_id': r.decision_id,
                    'workspace_id': r.workspace_id,
                    'summary': r.summary,
                    'rationale': r.rationale,
                    'created_at': r.created_at.isoformat(),
                    'relevance_score': r.relevance_score,
                    'user_id': r.user_id,
                    'tags': r.tags
                }
                for r in results
            ]

            logger.info(f"Unified search: {len(results)} results in {elapsed_ms:.1f}ms")

            return web.json_response({
                'results': results_json,
                'total': len(results),
                'query': query,
                'workspaces_searched': workspaces or 'all',
                'response_time_ms': elapsed_ms
            })

        except Exception as e:
            logger.error(f"Unified search error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def workspace_relationships(self, request):
        """
        Multi-workspace relationship traversal endpoint.

        Query params:
            decision_id: Starting decision ID (required)
            user_id: User identifier (required)
            include_workspaces: Include cross-workspace relations (default true)
            max_depth: Max traversal depth (default 3, ADHD-safe)

        Returns:
            Graph of related decisions

        Performance: <500ms for depth-3
        """
        try:
            decision_id = request.query.get('decision_id')
            user_id = request.query.get('user_id')

            if not decision_id or not user_id:
                return web.json_response(
                    {'error': 'decision_id and user_id are required'},
                    status=400
                )

            include_workspaces = request.query.get('include_workspaces', 'true').lower() == 'true'
            max_depth = int(request.query.get('max_depth', 3))

            # Execute relationship traversal
            start_time = datetime.now()
            graph = await self.unified_query_api.get_related_decisions(
                decision_id=int(decision_id),
                user_id=user_id,
                include_workspaces=include_workspaces,
                max_depth=max_depth
            )
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(f"Relationship traversal: {graph['total_nodes']} nodes in {elapsed_ms:.1f}ms")

            graph['response_time_ms'] = elapsed_ms
            return web.json_response(graph)

        except Exception as e:
            logger.error(f"Relationship traversal error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def workspace_summary(self, request):
        """
        Workspace aggregation endpoint.

        Query params:
            user_id: User identifier (required)

        Returns:
            List of workspace summaries with activity metrics

        Performance: <100ms
        """
        try:
            user_id = request.query.get('user_id')

            if not user_id:
                return web.json_response(
                    {'error': 'user_id is required'},
                    status=400
                )

            # Execute workspace summary
            start_time = datetime.now()
            summaries = await self.unified_query_api.get_workspace_summary(user_id)
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Convert to JSON
            summaries_json = [
                {
                    'workspace_id': s.workspace_id,
                    'name': s.name,
                    'total_decisions': s.total_decisions,
                    'recent_decisions_7d': s.recent_decisions_7d,
                    'total_progress': s.total_progress,
                    'in_progress_count': s.in_progress_count,
                    'last_activity': s.last_activity.isoformat() if s.last_activity else None
                }
                for s in summaries
            ]

            logger.info(f"Workspace summary: {len(summaries)} workspaces in {elapsed_ms:.1f}ms")

            return web.json_response({
                'workspaces': summaries_json,
                'total': len(summaries),
                'user_id': user_id,
                'response_time_ms': elapsed_ms
            })

        except Exception as e:
            logger.error(f"Workspace summary error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def start_server(self):
        """Start the enhanced HTTP server"""
        logger.info(f"🚀 Starting Enhanced ConPort Server on {self.host}:{self.port}")

        # Initialize connections
        await self.init_connections()

        # Create and start web server
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"✅ Enhanced ConPort API available at http://{self.host}:{self.port}")
        logger.info("📋 Features: Real PostgreSQL persistence + Redis caching + ADHD optimization")

        # Wait for shutdown signal
        await self.shutdown_event.wait()

        # Cleanup
        await self.close_connections()
        await runner.cleanup()
        logger.info("🛑 Enhanced ConPort Server stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Signal shutdown"""
        self.shutdown_event.set()

async def main():
    server = EnhancedConPortServer()

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
        loop.add_signal_handler(sig, server.signal_handler, sig, None)

    try:
        await server.start_server()
        return 0
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down")
        await server.shutdown()
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await server.shutdown()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
