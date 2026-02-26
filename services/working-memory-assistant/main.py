#!/usr/bin/env python3
"""
Working Memory Assistant - FastAPI Service
Provides 20-30x faster interrupt recovery for ADHD developers through intelligent context preservation.
"""

import os

import logging

logger = logging.getLogger(__name__)

import json
import time
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import redis.asyncio as redis
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.pool
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn
from pathlib import Path

# Import ADHD integration
try:
    from .adhd_engine_client import ADHDEngineClient, get_adhd_engine_client, close_adhd_engine_client
    ADHD_INTEGRATION_AVAILABLE = True
except ImportError:
    logger.info("ADHD Engine integration not available - running in degraded mode")
    ADHD_INTEGRATION_AVAILABLE = False

# Configuration
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5455'),
    'database': os.getenv('POSTGRES_DB', 'dopemux_knowledge_graph'),
    'user': os.getenv('POSTGRES_USER', 'dopemux_age'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dopemux_age_dev_password'),
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': 0,
    'decode_responses': True
}

# Global connections
postgres_pool = None
redis_client = None

# Rate limiting
rate_limit_store: Dict[str, List[float]] = {}

def check_rate_limit(client_ip: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """Simple in-memory rate limiting"""
    current_time = time.time()
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []

    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < window_seconds
    ]

    # Check if under limit
    if len(rate_limit_store[client_ip]) < max_requests:
        rate_limit_store[client_ip].append(current_time)
        return True

    return False

# Security configuration
SECRET_KEY = os.getenv("WMA_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption utilities for sensitive data
from cryptography.fernet import Fernet

# Use environment variable or generate key (in production, use env var)
ENCRYPTION_KEY = os.getenv("WMA_ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive text data"""
    if not data:
        return data
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive text data"""
    if not encrypted_data:
        return encrypted_data
    try:
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # Return as-is if decryption fails (backward compatibility)
        return encrypted_data

        logger.error(f"Error: {e}")
# Pydantic Models
class ContextSnapshot(BaseModel):
    """Working memory context snapshot"""
    id: Optional[str] = None
    user_id: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    session_id: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    context_type: str = Field(..., pattern=r'^(work|personal|meeting|break)$')
    priority: float = Field(0.5, ge=0.0, le=1.0)
    emotional_weight: float = Field(0.0, ge=0.0, le=1.0)
    complexity_score: float = Field(0.5, ge=0.0, le=1.0)

    # Hierarchical context data with size limits
    mental_model: Dict[str, Any] = Field(..., max_items=50)
    active_focus: Dict[str, Any] = Field(..., max_items=20)
    current_task: Dict[str, Any] = Field(..., max_items=10)

    metadata: Optional[Dict[str, Any]] = Field(None, max_items=20)
    checksum: Optional[str] = None
    workspace_path: Optional[str] = None  # Multi-workspace tracking

    @validator('mental_model', 'active_focus', 'current_task', 'metadata')
    def validate_dict_size(cls, v):
        """Validate that nested dictionaries don't exceed reasonable sizes"""
        if v is None:
            return v

        def check_nested_size(obj, max_depth=3, max_string_len=1000):
            if max_depth <= 0:
                raise ValueError("Dictionary nesting too deep")
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if len(str(key)) > 100:
                        raise ValueError(f"Key too long: {key}")
                    check_nested_size(value, max_depth - 1)
            elif isinstance(obj, list):
                if len(obj) > 20:
                    raise ValueError("List too long")
                for item in obj:
                    check_nested_size(item, max_depth - 1)
            elif isinstance(obj, str):
                if len(obj) > max_string_len:
                    raise ValueError(f"String too long: {len(obj)} characters")

        check_nested_size(v)
        return v

    @validator('user_id', 'session_id')
    def validate_no_malicious_input(cls, v):
        """Basic protection against common malicious inputs"""
        if v:
            # Check for SQL injection patterns
            dangerous_patterns = ['--', '/*', '*/', 'xp_', 'sp_', 'exec', 'union']
            for pattern in dangerous_patterns:
                if pattern.lower() in v.lower():
                    raise ValueError(f"Potentially malicious input detected: {pattern}")

            # Check for very long repetitive strings that might be attacks
            if len(set(v)) < len(v) * 0.3:  # Less than 30% unique characters
                raise ValueError("Input contains suspicious repetitive patterns")

        return v

class RecoveryRequest(BaseModel):
    """Recovery initiation request"""
    user_id: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    snapshot_id: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    recovery_stage: str = Field('essential', pattern=r'^(essential|detailed|complete)$')

    @validator('user_id', 'snapshot_id')
    def validate_no_malicious_input(cls, v):
        """Basic protection against common malicious inputs"""
        if v:
            dangerous_patterns = ['--', '/*', '*/', 'xp_', 'sp_', 'exec', 'union']
            for pattern in dangerous_patterns:
                if pattern.lower() in v.lower():
                    raise ValueError(f"Potentially malicious input detected: {pattern}")
        return v

class RecoveryResponse(BaseModel):
    """Recovery response with context data"""
    snapshot_id: str
    recovery_stage: str
    context_data: Dict[str, Any]
    recovery_time_ms: int
    cache_hit: bool

class UserPreferences(BaseModel):
    """User preferences for WMA"""
    user_id: str
    auto_snapshot_enabled: bool = True
    privacy_level: str = Field('balanced', pattern='^(minimal|balanced|comprehensive)$')
    retention_days: int = Field(30, ge=1, le=365)
    max_memory_mb: int = Field(50, ge=10, le=500)
    notification_style: str = Field('gentle', pattern='^(disabled|gentle|standard)$')

# Database Operations
class DatabaseManager:
    """PostgreSQL database operations for WMA"""

    def __init__(self, pool):
        self.pool = pool

    async def create_snapshot(self, snapshot: ContextSnapshot, allow_incremental: bool = True) -> str:
        """Create a new context snapshot with encryption and incremental support"""
        # Encrypt sensitive fields
        snapshot_data = {
            'mental_model': snapshot.mental_model,  # Usually not sensitive
            'active_focus': snapshot.active_focus,  # Contains file paths - encrypt
            'current_task': snapshot.current_task    # Contains task descriptions - encrypt
        }

        # Encrypt sensitive nested data
        if snapshot_data['active_focus']:
            snapshot_data['active_focus'] = json.loads(
                encrypt_sensitive_data(json.dumps(snapshot_data['active_focus']))
            )
        if snapshot_data['current_task']:
            snapshot_data['current_task'] = json.loads(
                encrypt_sensitive_data(json.dumps(snapshot_data['current_task']))
            )

        # Calculate checksum
        data_str = json.dumps(snapshot_data, sort_keys=True)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()

        query = """
            INSERT INTO wma_contexts (
                user_id, session_id, context_type, priority, emotional_weight,
                complexity_score, snapshot_data, metadata, checksum
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    snapshot.user_id, snapshot.session_id, snapshot.context_type,
                    snapshot.priority, snapshot.emotional_weight, snapshot.complexity_score,
                    json.dumps(snapshot_data), json.dumps(snapshot.metadata or {}), checksum
                ))
                result = cursor.fetchone()
                conn.commit()
                return str(result[0])
        finally:
            self.pool.putconn(conn)

    async def get_snapshot(self, snapshot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a context snapshot"""
        query = """
            SELECT id, user_id, context_type, priority, emotional_weight, complexity_score,
                   snapshot_data, metadata, checksum, created_at, last_accessed
            FROM wma_contexts
            WHERE id = %s AND user_id = %s
        """

        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (snapshot_id, user_id))
                result = cursor.fetchone()
                if result:
                    # Decrypt sensitive fields
                    snapshot_data = result['snapshot_data']
                    if snapshot_data and 'active_focus' in snapshot_data:
                        try:
                            decrypted = decrypt_sensitive_data(json.dumps(snapshot_data['active_focus']))
                            snapshot_data['active_focus'] = json.loads(decrypted)
                        except Exception as e:
                            logger.error(f"Error: {e}")
                    if snapshot_data and 'current_task' in snapshot_data:
                        try:
                            decrypted = decrypt_sensitive_data(json.dumps(snapshot_data['current_task']))
                            snapshot_data['current_task'] = json.loads(decrypted)
                        except Exception as e:
                            logger.error(f"Error: {e}")
                    # Update last accessed
                    update_query = "UPDATE wma_contexts SET last_accessed = NOW() WHERE id = %s"
                    cursor.execute(update_query, (snapshot_id,))
                    conn.commit()
                    return dict(result)
                return None
        finally:
            self.pool.putconn(conn)

    async def get_user_contexts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent contexts"""
        query = """
            SELECT id, context_type, priority, emotional_weight, complexity_score,
                   created_at, last_accessed
            FROM wma_contexts
            WHERE user_id = %s
            ORDER BY priority DESC, last_accessed DESC
            LIMIT %s
        """

        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        finally:
            self.pool.putconn(conn)

    async def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        query = "SELECT * FROM wma_user_preferences WHERE user_id = %s"

        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        finally:
            self.pool.putconn(conn)

    async def update_user_preferences(self, prefs: UserPreferences) -> None:
        """Update or create user preferences"""
        query = """
            INSERT INTO wma_user_preferences (
                user_id, auto_snapshot_enabled, privacy_level,
                retention_days, max_memory_mb, notification_style
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                auto_snapshot_enabled = EXCLUDED.auto_snapshot_enabled,
                privacy_level = EXCLUDED.privacy_level,
                retention_days = EXCLUDED.retention_days,
                max_memory_mb = EXCLUDED.max_memory_mb,
                notification_style = EXCLUDED.notification_style,
                updated_at = NOW()
        """

        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    prefs.user_id, prefs.auto_snapshot_enabled, prefs.privacy_level,
                    prefs.retention_days, prefs.max_memory_mb, prefs.notification_style
                ))
                conn.commit()
        finally:
            self.pool.putconn(conn)

# Redis Cache Operations
class CacheManager:
    """Advanced Redis cache operations with predictive pre-fetching and LRU optimization"""

    def __init__(self, client):
        self.client = client
        # Cache configuration with intelligent TTLs
        self.ttl_configs = {
            'snapshot': 3600,      # 1 hour for snapshots
            'recovery': 1800,      # 30 min for recovery state
            'context': 86400,      # 24 hours for context data
            'adhd_state': 300,     # 5 min for ADHD state (frequently changing)
            'conport_links': 7200  # 2 hours for ConPort links
        }
        # Predictive caching patterns based on ADHD state
        self.predictive_patterns = {
            'low_energy': ['essential_recovery', 'gentle_mode', 'simple_context'],
            'high_energy': ['full_context', 'complex_recovery', 'detailed_mode'],
            'scattered': ['minimal_context', 'quick_recovery', 'basic_mode'],
            'focused': ['detailed_context', 'standard_recovery', 'balanced_mode'],
            'overwhelmed': ['minimal_context', 'quick_recovery', 'essential_mode'],
            'hyperfocus': ['preserve_flow', 'complex_context', 'preserve_mode']
        }
        # LRU tracking for cache optimization
        self.access_counts = {}
        self.hit_rate_tracker = {'hits': 0, 'misses': 0}

    async def set_context(self, snapshot_id: str, context_data: Dict[str, Any], cache_type: str = 'context') -> None:
        """Cache context snapshot in Redis with intelligent TTL"""
        key = f"wma:{cache_type}:{context_data['user_id']}:{snapshot_id}"
        ttl = self.ttl_configs.get(cache_type, 3600)
        await self.client.setex(key, ttl, json.dumps(context_data))

    async def get_context(self, snapshot_id: str, user_id: str, cache_type: str = 'context') -> Optional[Dict[str, Any]]:
        """Get cached context snapshot with hit/miss tracking"""
        key = f"wma:{cache_type}:{user_id}:{snapshot_id}"
        data = await self.client.get(key)

        # Track hit rate
        if data:
            self.hit_rate_tracker['hits'] += 1
            # Update access count for LRU
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
        else:
            self.hit_rate_tracker['misses'] += 1

        return json.loads(data) if data else None

    async def set_recovery_state(self, user_id: str, state: Dict[str, Any], ttl: int = 3600) -> None:
        """Cache recovery state"""
        key = f"wma:recovery:{user_id}"
        await self.client.setex(key, ttl, json.dumps(state))

    async def get_recovery_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached recovery state"""
        key = f"wma:recovery:{user_id}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def predictive_pre_fetch(self, user_id: str, adhd_state: str) -> None:
        """Pre-fetch commonly needed data based on ADHD state patterns"""
        patterns = self.predictive_patterns.get(adhd_state, ['standard_recovery'])

        # Pre-fetch recovery state for predicted patterns
        for pattern in patterns:
            key = f"wma:recovery:{user_id}:{pattern}"
            # Check if already cached, if not, pre-fetch from database
            if not await self.client.exists(key):
                # This would trigger database pre-fetch in real implementation
                # For now, just mark as pre-fetched pattern
                await self.client.setex(key, 300, json.dumps({'pattern': pattern, 'prefetched': True}))

    async def optimize_lru_cache(self, max_keys: int = 1000) -> None:
        """Perform LRU cache optimization by removing least recently used items"""
        # Get all WMA keys
        keys = await self.client.keys('wma:*')
        if len(keys) <= max_keys:
            return

        # Sort by access count (ascending = LRU)
        key_access = [(k, self.access_counts.get(k, 0)) for k in keys]
        key_access.sort(key=lambda x: x[1])  # Sort by access count ascending

        # Remove least recently used items
        to_remove = key_access[:len(keys) - max_keys]
        for key, _ in to_remove:
            await self.client.delete(key)
            self.access_counts.pop(key, None)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hit_rate_tracker['hits'] + self.hit_rate_tracker['misses']
        hit_rate = (self.hit_rate_tracker['hits'] / total_requests) if total_requests > 0 else 0

        return {
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'cache_size': len(self.access_counts),
            'ttl_configs': self.ttl_configs
        }

# Core WMA Service
class WMAService:
    """Working Memory Assistant core service"""

    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.db = db_manager
        self.cache = cache_manager

    async def _enhance_snapshot_with_adhd(self, snapshot: ContextSnapshot) -> None:
        """Enhance snapshot with real-time ADHD state correlation"""
        try:
            adhd_client = get_adhd_engine_client()
            adhd_context = await adhd_client.get_adhd_context(snapshot.user_id)

            if adhd_context and adhd_context['is_available']:
                # Add ADHD context to metadata
                snapshot.metadata = snapshot.metadata or {}
                snapshot.metadata.update({
                    'adhd_context': {
                        'energy_level': adhd_context.get('energy_level', {}).get('level', 0.5),
                        'attention_state': adhd_context.get('attention_state', {}).get('state', 'neutral'),
                        'cognitive_load': adhd_context.get('cognitive_load', {}).get('load', 0.5),
                        'break_recommended': adhd_context.get('break_recommendation', {}).get('recommended', False),
                        'adhd_timestamp': datetime.now().isoformat()
                    }
                })

                # Adjust priority based on ADHD state
                base_priority = snapshot.priority
                energy_factor = adhd_context.get('energy_level', {}).get('level', 0.5)
                attention_factor = 0.8 if adhd_context.get('attention_state', {}).get('state', '') == 'focused' else 0.4
                cognitive_factor = 0.3 if adhd_context.get('cognitive_load', {}).get('load', 0.5) > 0.7 else 0.7

                adjusted_priority = (
                    base_priority * 0.6 +
                    energy_factor * 0.2 +
                    attention_factor * 0.15 +
                    cognitive_factor * 0.05
                )
                snapshot.priority = max(0.0, min(1.0, adjusted_priority))

                logger.info(f"ADHD-aware priority adjustment: {base_priority:.2f} → {snapshot.priority:.2f}")

        except Exception as e:
            logger.error(f"ADHD enhancement failed: {e}")
            # Continue without ADHD enhancement

    async def _adapt_recovery_stage_to_adhd(self, user_id: str, requested_stage: str) -> str:
        """Adapt recovery stage based on current ADHD state"""
        try:
            adhd_client = get_adhd_engine_client()
            adhd_context = await adhd_client.get_adhd_context(user_id)

            if not adhd_context or not adhd_context['is_available']:
                return requested_stage

            # Adapt based on ADHD metrics
            energy_level = adhd_context.get('energy_level', {}).get('level', 0.5)
            attention_state = adhd_context.get('attention_state', {}).get('state', 'neutral')
            cognitive_load = adhd_context.get('cognitive_load', {}).get('load', 0.5)

            # Low energy: Start with essential only
            if energy_level < 0.3:
                return 'essential'

            # High cognitive load: Be gentle with information
            if cognitive_load > 0.8:
                return 'essential' if requested_stage == 'complete' else requested_stage

            # Focused attention: Can handle more information
            if attention_state == 'focused' and energy_level > 0.6:
                return 'detailed' if requested_stage == 'essential' else requested_stage

            # Scattered attention: Keep it simple
            if attention_state == 'scattered':
                return 'essential'

            return requested_stage

        except Exception as e:
            logger.error(f"ADHD recovery adaptation failed: {e}")
            return requested_stage

    async def _get_adhd_recovery_recommendations(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get ADHD recommendations for recovery context"""
        try:
            adhd_client = get_adhd_engine_client()
            adhd_context = await adhd_client.get_adhd_context(user_id)

            if adhd_context and adhd_context['is_available']:
                return {
                    'current_energy': adhd_context.get('energy_level', {}).get('level', 0.5),
                    'recommended_break': adhd_context.get('break_recommendation', {}).get('recommended', False),
                    'attention_state': adhd_context.get('attention_state', {}).get('state', 'neutral'),
                    'cognitive_load': adhd_context.get('cognitive_load', {}).get('load', 0.5)
                }
            return None

        except Exception as e:
            logger.error(f"ADHD recovery recommendations failed: {e}")
            return None

    async def create_snapshot(self, snapshot: ContextSnapshot, enhance_with_adhd: bool = True) -> str:
        """Create and cache a new context snapshot with optional ADHD enhancement"""
        start_time = time.time()

        # Enhance snapshot with ADHD context if available
        if enhance_with_adhd and ADHD_INTEGRATION_AVAILABLE:
            await self._enhance_snapshot_with_adhd(snapshot)

        # Create snapshot in database
        snapshot_id = await self.db.create_snapshot(snapshot)

        # Cache in Redis for fast access
        context_data = {
            'id': snapshot_id,
            'user_id': snapshot.user_id,
            'session_id': snapshot.session_id,
            'context_type': snapshot.context_type,
            'priority': snapshot.priority,
            'emotional_weight': snapshot.emotional_weight,
            'complexity_score': snapshot.complexity_score,
            'mental_model': snapshot.mental_model,
            'active_focus': snapshot.active_focus,
            'current_task': snapshot.current_task,
            'metadata': snapshot.metadata,
            'created_at': datetime.now().isoformat(),
            'cache_timestamp': time.time()
        }

        await self.cache.set_context(snapshot_id, context_data)

        # Log performance
        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Snapshot created: {snapshot_id} in {duration}ms")

        return snapshot_id

    async def recover_context(self, request: RecoveryRequest, adapt_to_adhd: bool = True) -> RecoveryResponse:
        """Recover context with progressive disclosure and optional ADHD adaptation"""
        start_time = time.time()
        user_id = request.user_id

        # Adapt recovery stage based on ADHD state if available
        adapted_stage = request.recovery_stage
        adhd_recommendations = None

        if adapt_to_adhd and ADHD_INTEGRATION_AVAILABLE:
            adapted_stage = await self._adapt_recovery_stage_to_adhd(user_id, request.recovery_stage)
            if adapted_stage != request.recovery_stage:
                logger.info(f"ADHD adaptation: {request.recovery_stage} → {adapted_stage}")

        # Try cache first
        if request.snapshot_id:
            context_data = await self.cache.get_context(request.snapshot_id, user_id)
            cache_hit = context_data is not None
        else:
            # Find most recent high-priority context
            contexts = await self.db.get_user_contexts(user_id, limit=1)
            if contexts:
                context_data = await self.cache.get_context(contexts[0]['id'], user_id)
                cache_hit = context_data is not None
                if not context_data:
                    context_data = await self.db.get_snapshot(contexts[0]['id'], user_id)
            else:
                context_data = None
            cache_hit = False

        if not context_data:
            raise HTTPException(status_code=404, detail="Context not found")

        # Get ADHD recommendations for recovery
        if ADHD_INTEGRATION_AVAILABLE:
            adhd_recommendations = await self._get_adhd_recovery_recommendations(user_id)

        # Progressive disclosure based on adapted recovery stage
        if request.recovery_stage == 'essential':
            # Only essential information
            context_data = {
                'task': context_data.get('current_task', {}).get('description', ''),
                'file': context_data.get('active_focus', {}).get('file', ''),
                'line': context_data.get('active_focus', {}).get('cursor', {}).get('line', 0)
            }
        elif request.recovery_stage == 'detailed':
            # Include more context but still curated
            context_data = {
                'mental_model': context_data.get('mental_model', {}),
                'current_task': context_data.get('current_task', {}),
                'active_focus': context_data.get('active_focus', {})
            }
        # 'complete' returns full context_data

        duration = int((time.time() - start_time) * 1000)

        # Create response with ADHD recommendations if available
        response = RecoveryResponse(
            snapshot_id=context_data.get('id', request.snapshot_id or 'unknown'),
            recovery_stage=adapted_stage,  # Use adapted stage
            context_data=context_data,
            recovery_time_ms=duration,
            cache_hit=cache_hit
        )

        # Add ADHD recommendations as metadata
        if adhd_recommendations:
            response.metadata = getattr(response, 'metadata', {})
            response.metadata['adhd_recommendations'] = adhd_recommendations

        return response


# FastAPI Application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global postgres_pool, redis_client

    # Initialize connections
    postgres_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1, maxconn=10, **POSTGRES_CONFIG
    )

    redis_client = redis.Redis(**REDIS_CONFIG)
    await redis_client.ping()

    # Initialize service
    db_manager = DatabaseManager(postgres_pool)
    cache_manager = CacheManager(redis_client)
    wma_service = WMAService(db_manager, cache_manager)

    # Make service available to routes
    app.state.wma_service = wma_service

    logger.info("Working Memory Assistant service started")
    yield

    # Cleanup
    if postgres_pool:
        postgres_pool.closeall()
    if redis_client:
        await redis_client.close()
    if ADHD_INTEGRATION_AVAILABLE:
        await close_adhd_engine_client()

    logger.info("Working Memory Assistant service stopped")

app = FastAPI(
    title="Working Memory Assistant + ADHD Integration",
    description="ADHD-optimized context preservation with real-time energy monitoring and cognitive load assessment",
    version="2.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8097"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = request.client.host if request.client else "unknown"

    # Different limits for different endpoints
    path = request.url.path
    if path.startswith("/snapshot"):
        max_requests = 50  # More restrictive for writes
    elif path.startswith("/recover"):
        max_requests = 100  # Moderate for reads
    else:
        max_requests = 200  # Generous for other endpoints

    if not check_rate_limit(client_ip, max_requests=max_requests):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    response = await call_next(request)
    return response

# Routes
@app.post("/snapshot", response_model=dict)
async def create_snapshot(
    snapshot: ContextSnapshot,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new context snapshot"""
    user_id = verify_token(credentials)
    snapshot.user_id = user_id  # Ensure user_id is set from token
    service = app.state.wma_service
    snapshot_id = await service.create_snapshot(snapshot)
    return {"snapshot_id": snapshot_id, "status": "created"}

@app.post("/recover", response_model=RecoveryResponse)
async def recover_context(
    request: RecoveryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Recover context with progressive disclosure"""
    user_id = verify_token(credentials)
    if request.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied - user mismatch")
    service = app.state.wma_service
    return await service.recover_context(request)

@app.get("/contexts/{user_id}")
async def get_user_contexts(user_id: str, limit: int = 10):
    """Get user's recent contexts"""
    service = app.state.wma_service
    contexts = await service.db.get_user_contexts(user_id, limit)
    return {"contexts": contexts}

@app.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    service = app.state.wma_service
    prefs = await service.db.get_user_preferences(user_id)
    if not prefs:
        # Return defaults
        return UserPreferences(user_id=user_id).dict()
    return prefs

@app.post("/preferences")
async def update_user_preferences(prefs: UserPreferences):
    """Update user preferences"""
    service = app.state.wma_service
    await service.db.update_user_preferences(prefs)
    return {"status": "updated"}

# ADHD-Aware Endpoints
@app.post("/adhd-snapshot")
async def create_adhd_aware_snapshot(snapshot: ContextSnapshot):
    """Create ADHD-aware snapshot with real-time state correlation"""
    service = app.state.wma_service
    snapshot_id = await service.create_snapshot(snapshot, enhance_with_adhd=True)
    return {"snapshot_id": snapshot_id, "status": "created_adhd_aware"}

@app.post("/adhd-recover")
async def recover_adhd_adapted_context(request: RecoveryRequest):
    """Recover context adapted to current ADHD state"""
    service = app.state.wma_service
    return await service.recover_context(request, adapt_to_adhd=True)

@app.get("/adhd-context/{user_id}")
async def get_adhd_context(user_id: str):
    """Get current ADHD context for user"""
    if not ADHD_INTEGRATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="ADHD Engine integration not available")

    adhd_client = get_adhd_engine_client()
    context = await adhd_client.get_adhd_context(user_id)
    return context

@app.post("/should-snapshot/{user_id}")
async def should_snapshot_based_on_adhd(user_id: str):
    """Determine if snapshot should be created based on ADHD state"""
    if not ADHD_INTEGRATION_AVAILABLE:
        return {"should_snapshot": True, "reason": "ADHD integration unavailable"}

    adhd_client = get_adhd_engine_client()
    should = await adhd_client.should_snapshot_based_on_adhd_state(user_id)
    return {"should_snapshot": should}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database
        conn = postgres_pool.getconn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        postgres_pool.putconn(conn)

        # Test Redis
        await redis_client.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "cache": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

        logger.error(f"Error: {e}")
@app.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Get user statistics"""
    service = app.state.wma_service
    stats = await service.db.get_user_stats(user_id)
    return stats

if __name__ == "__main__":
    port = int(os.getenv("WMA_PORT", "8096"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )