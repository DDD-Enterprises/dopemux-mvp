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

# Worktree multi-instance support
from instance_detector import SimpleInstanceDetector

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Configuration
        self.postgres_url = os.getenv(
            'DATABASE_URL',
            'postgresql://dopemux:dopemux_secure_2024@postgres-primary:5432/conport'
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://redis-primary:6379')

        # ADHD-specific settings
        self.auto_save_interval = 30  # seconds
        self.context_cache_ttl = 300  # 5 minutes

        self.shutdown_event = asyncio.Event()
        self.auto_save_task = None

        # Setup routes
        self.setup_routes()

    async def init_connections(self):
        """Initialize database and Redis connections"""
        try:
            # PostgreSQL connection pool
            self.db_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=1,
                max_size=5,
                command_timeout=60
            )
            logger.info("✅ PostgreSQL connection pool established")

            # Redis connection
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis.ping()
            logger.info("✅ Redis connection established")

            # Start auto-save task for ADHD context preservation
            self.auto_save_task = asyncio.create_task(self.auto_save_loop())

        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise

    async def close_connections(self):
        """Cleanup database and Redis connections"""
        if self.auto_save_task:
            self.auto_save_task.cancel()

        if self.redis:
            await self.redis.close()

        if self.db_pool:
            await self.db_pool.close()

        logger.info("🔌 Connections closed")

    def setup_routes(self):
        """Setup HTTP API routes for ConPort access"""
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

        # Custom data endpoints (generic key-value store)
        self.app.router.add_post('/api/custom_data', self.save_custom_data)
        self.app.router.add_get('/api/custom_data', self.get_custom_data)
        self.app.router.add_delete('/api/custom_data', self.delete_custom_data)

        # MCP compatibility endpoint
        self.app.router.add_post('/mcp', self.mcp_endpoint)

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
            return web.json_response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }, status=503)

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
                    # Create default context for new workspace/instance
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

            logger.info(f"💡 Logged decision: {data.get('summary')}")

            return web.json_response({
                'status': 'logged',
                'decision': decision_entry
            })

        except Exception as e:
            logger.error(f"❌ Error logging decision: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_decisions(self, request):
        """Get decision history for workspace"""
        workspace_id = request.query.get('workspace_id')
        limit = int(request.query.get('limit', 10))

        try:
            # Try cache first
            cache_key = f"decisions:{workspace_id}:{limit}"
            cached = await self.redis.get(cache_key)

            if cached:
                return web.json_response(json.loads(cached))

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, workspace_id, summary, rationale, alternatives,
                           tags, confidence_level, decision_type, created_at
                    FROM decisions
                    WHERE workspace_id = $1 OR $1 IS NULL
                    ORDER BY created_at DESC
                    LIMIT $2
                """, workspace_id, limit)

                decisions = []
                for row in rows:
                    decision = dict(row)
                    decision['id'] = str(decision['id'])  # Convert UUID to string
                    decision['created_at'] = decision['created_at'].isoformat()
                    decision['alternatives'] = json.loads(decision['alternatives'])
                    decisions.append(decision)

            result = {
                'workspace_id': workspace_id,
                'decisions': decisions,
                'count': len(decisions)
            }

            # Cache results
            await self.redis.setex(cache_key, 300, json.dumps(result))

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting decisions: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def log_progress(self, request):
        """Log progress on current work with worktree instance routing"""
        data = await request.json()

        try:
            progress_id = str(uuid.uuid4())
            status = data.get('status', 'PLANNED')
            workspace_id = data.get('workspace_id')

            # Worktree multi-instance routing
            # IN_PROGRESS/PLANNED → isolated to current instance
            # COMPLETED/BLOCKED/CANCELLED → shared across all instances
            current_instance_id = SimpleInstanceDetector.get_instance_id()

            if SimpleInstanceDetector.is_isolated_status(status):
                # Isolated: Only visible in this worktree
                final_instance_id = current_instance_id
            else:
                # Shared: Visible in all worktrees
                final_instance_id = None

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO progress_entries
                    (id, workspace_id, instance_id, description, status, percentage,
                     linked_decision_id, priority, estimated_hours)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, progress_id,
                    workspace_id,
                    final_instance_id,
                    data.get('description'),
                    status,
                    data.get('percentage', 0),
                    data.get('linked_decision_id'),
                    data.get('priority', 'medium'),
                    data.get('estimated_hours'))

                # Get the inserted progress entry
                row = await conn.fetchrow("""
                    SELECT * FROM progress_entries WHERE id = $1
                """, progress_id)

                progress_entry = dict(row)
                progress_entry['id'] = str(progress_entry['id'])  # Convert UUID to string
                if progress_entry['linked_decision_id']:
                    progress_entry['linked_decision_id'] = str(progress_entry['linked_decision_id'])
                progress_entry['created_at'] = progress_entry['created_at'].isoformat()
                progress_entry['updated_at'] = progress_entry['updated_at'].isoformat()
                if progress_entry['completed_at']:
                    progress_entry['completed_at'] = progress_entry['completed_at'].isoformat()

            # Invalidate caches
            workspace_id = data.get('workspace_id')
            if workspace_id:
                await self.redis.delete(f"progress:{workspace_id}")
                await self.redis.delete(f"active_work:{workspace_id}")

            logger.info(f"📊 Progress logged: {data.get('description')} ({data.get('status')})")

            return web.json_response({
                'status': 'logged',
                'progress': progress_entry
            })

        except Exception as e:
            logger.error(f"❌ Error logging progress: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_progress(self, request):
        """Get current progress entries with worktree instance filtering"""
        workspace_id = request.query.get('workspace_id')
        status_filter = request.query.get('status_filter')
        limit = int(request.query.get('limit', 10))

        try:
            # Worktree multi-instance support
            current_instance_id = SimpleInstanceDetector.get_instance_id()

            cache_key = f"progress:{workspace_id}:{status_filter}:{limit}:{current_instance_id}"
            cached = await self.redis.get(cache_key)

            if cached:
                return web.json_response(json.loads(cached))

            # Multi-instance query:
            # Show shared tasks (instance_id IS NULL) + current instance tasks
            query = """
                SELECT * FROM progress_entries
                WHERE ($1::text IS NULL OR workspace_id = $1)
                  AND ($2::text IS NULL OR status = $2)
                  AND (instance_id IS NULL OR instance_id = $3)
                ORDER BY created_at DESC
                LIMIT $4
            """

            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(query, workspace_id, status_filter, current_instance_id, limit)

                progress_items = []
                for row in rows:
                    item = dict(row)
                    item['id'] = str(item['id'])  # Convert UUID to string
                    if item['linked_decision_id']:
                        item['linked_decision_id'] = str(item['linked_decision_id'])
                    item['created_at'] = item['created_at'].isoformat()
                    item['updated_at'] = item['updated_at'].isoformat()
                    if item['completed_at']:
                        item['completed_at'] = item['completed_at'].isoformat()
                    progress_items.append(item)

            result = {
                'progress_items': progress_items,
                'filter': status_filter,
                'count': len(progress_items)
            }

            # Cache results
            await self.redis.setex(cache_key, 300, json.dumps(result))

            return web.json_response(result)

        except Exception as e:
            logger.error(f"❌ Error getting progress: {e}")
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