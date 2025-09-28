"""
Serena v2 Navigation Cache

Redis-based caching for LSP responses, symbol lookups, and navigation state.
ADHD-optimized with intelligent prefetching and context preservation.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NavigationCacheConfig(BaseModel):
    """Configuration for navigation cache."""
    redis_url: str = "redis://localhost:6379"
    db_index: int = 1  # Separate from ConPort cache
    default_ttl: int = 300  # 5 minutes
    symbol_ttl: int = 600   # 10 minutes for symbols
    definition_ttl: int = 1800  # 30 minutes for definitions
    reference_ttl: int = 900   # 15 minutes for references
    max_cache_size: int = 10000
    key_prefix: str = "serena:v2:nav"


class NavigationCache:
    """
    Navigation-specific cache with ADHD optimizations.

    Features:
    - Intelligent TTL based on content type and stability
    - Context-aware prefetching for smooth navigation
    - Progressive cache warming for large codebases
    - Navigation breadcrumb preservation
    - Focus session state persistence
    """

    def __init__(self, config: NavigationCacheConfig):
        self.config = config
        self.client: Optional[redis.Redis] = None
        self._initialized = False

        # Navigation state tracking
        self.current_session = {}
        self.navigation_history = []
        self.focus_context = {}
        self.prefetch_patterns = {}

    async def initialize(self) -> None:
        """Initialize Redis connection and navigation tracking."""
        if self._initialized:
            return

        try:
            self.client = redis.from_url(
                self.config.redis_url,
                db=self.config.db_index,
                decode_responses=True,
                retry_on_error=[redis.BusyLoadingError],
                health_check_interval=30
            )

            # Test connection
            await self.client.ping()

            # Initialize session tracking
            self.current_session = {
                "session_id": f"nav_{datetime.now().timestamp()}",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "workspace_path": None,
                "active_files": [],
                "focus_mode": False
            }

            self._initialized = True
            logger.info(f"🚀 Navigation cache initialized: {self.config.redis_url}")

        except Exception as e:
            logger.error(f"Failed to initialize navigation cache: {e}")
            raise RuntimeError(f"Navigation cache initialization failed: {e}")

    def _generate_cache_key(self, category: str, file_path: str, extra: str = "") -> str:
        """Generate consistent cache keys for navigation data."""
        # Normalize file path for consistent caching
        normalized_path = str(Path(file_path).resolve())
        path_hash = hashlib.sha256(normalized_path.encode()).hexdigest()[:12]

        if extra:
            return f"{self.config.key_prefix}:{category}:{path_hash}:{extra}"
        else:
            return f"{self.config.key_prefix}:{category}:{path_hash}"

    # LSP Response Caching

    async def get_navigation_result(self, cache_key: str) -> Optional[Any]:
        """Get cached navigation result."""
        try:
            cached_data = await self.client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)

                # Check freshness for ADHD users (stale data can be confusing)
                cached_time = datetime.fromisoformat(data.get("cached_at", ""))
                age_minutes = (datetime.now(timezone.utc) - cached_time).total_seconds() / 60

                if age_minutes < 60:  # Fresh within 1 hour
                    logger.debug(f"🎯 Navigation cache hit: {cache_key[:50]}...")
                    return data.get("result")

                # Remove stale data
                await self.client.delete(cache_key)

            return None

        except Exception as e:
            logger.error(f"Failed to get navigation result: {e}")
            return None

    async def cache_navigation_result(
        self,
        cache_key: str,
        result: Any,
        ttl: int = None
    ) -> bool:
        """Cache navigation result with metadata."""
        cache_ttl = ttl or self.config.default_ttl

        cache_data = {
            "result": result,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "ttl": cache_ttl,
            "result_size": len(str(result)) if result else 0
        }

        try:
            await self.client.setex(
                cache_key,
                cache_ttl,
                json.dumps(cache_data, default=str)
            )

            logger.debug(f"💾 Cached navigation result: {cache_key[:50]}... (TTL: {cache_ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to cache navigation result: {e}")
            return False

    # Symbol and Definition Specific Caching

    async def cache_file_symbols(
        self,
        file_path: str,
        symbols: List[Dict[str, Any]],
        language: str
    ) -> bool:
        """Cache file symbols with intelligent TTL."""
        cache_key = self._generate_cache_key("symbols", file_path, language)

        # Intelligent TTL based on file type and project patterns
        if file_path.endswith(('.py', '.js', '.ts')):
            # Source files change more frequently
            ttl = self.config.symbol_ttl
        elif file_path.endswith(('.md', '.txt', '.json')):
            # Config/doc files change less frequently
            ttl = self.config.symbol_ttl * 2
        else:
            ttl = self.config.default_ttl

        return await self.cache_navigation_result(cache_key, symbols, ttl)

    async def get_file_symbols(self, file_path: str, language: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached file symbols."""
        cache_key = self._generate_cache_key("symbols", file_path, language)
        return await self.get_navigation_result(cache_key)

    async def cache_definition(
        self,
        file_path: str,
        line: int,
        character: int,
        definition: List[Dict[str, Any]]
    ) -> bool:
        """Cache definition lookup result."""
        cache_key = self._generate_cache_key("definition", file_path, f"{line}:{character}")
        return await self.cache_navigation_result(cache_key, definition, self.config.definition_ttl)

    async def get_definition(
        self,
        file_path: str,
        line: int,
        character: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached definition."""
        cache_key = self._generate_cache_key("definition", file_path, f"{line}:{character}")
        return await self.get_navigation_result(cache_key)

    # ADHD-Optimized Session Management

    async def save_navigation_session(
        self,
        workspace_path: str,
        session_data: Dict[str, Any]
    ) -> str:
        """Save navigation session for ADHD context preservation."""
        session_id = self.current_session["session_id"]
        session_key = f"{self.config.key_prefix}:session:{session_id}"

        enhanced_session = {
            **session_data,
            "workspace_path": workspace_path,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "navigation_history": self.navigation_history[-10:],  # Last 10 navigation actions
            "focus_context": self.focus_context,
            "cache_stats": await self._get_cache_stats()
        }

        try:
            # Save session with 24-hour TTL
            await self.client.setex(
                session_key,
                86400,  # 24 hours
                json.dumps(enhanced_session, default=str)
            )

            logger.info(f"💾 Navigation session saved: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to save navigation session: {e}")
            return session_id

    async def restore_navigation_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Restore navigation session for ADHD context continuity."""
        session_key = f"{self.config.key_prefix}:session:{session_id}"

        try:
            cached_session = await self.client.get(session_key)
            if cached_session:
                session_data = json.loads(cached_session)

                # Restore navigation state
                self.navigation_history = session_data.get("navigation_history", [])
                self.focus_context = session_data.get("focus_context", {})

                logger.info(f"📂 Navigation session restored: {session_id}")
                return session_data

            return None

        except Exception as e:
            logger.error(f"Failed to restore navigation session: {e}")
            return None

    # Focus Mode and Context Tracking

    async def set_focus_context(
        self,
        file_path: str,
        focus_area: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """Cache focus context for ADHD concentration support."""
        focus_key = self._generate_cache_key("focus", file_path, "context")

        focus_data = {
            **focus_area,
            "set_at": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
            "session_id": self.current_session["session_id"]
        }

        try:
            await self.client.setex(
                focus_key,
                ttl,
                json.dumps(focus_data, default=str)
            )

            # Update local focus context
            self.focus_context[file_path] = focus_area

            logger.debug(f"🎯 Focus context set for {Path(file_path).name}")
            return True

        except Exception as e:
            logger.error(f"Failed to set focus context: {e}")
            return False

    async def get_focus_context(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get focus context for file."""
        focus_key = self._generate_cache_key("focus", file_path, "context")
        return await self.get_navigation_result(focus_key)

    async def track_navigation_action(
        self,
        action_type: str,
        file_path: str,
        location: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Track navigation action for breadcrumb intelligence."""
        navigation_entry = {
            "action": action_type,
            "file_path": file_path,
            "location": location or {},
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.current_session["session_id"]
        }

        # Add to local history
        self.navigation_history.append(navigation_entry)

        # Keep history manageable for ADHD users
        if len(self.navigation_history) > 50:
            self.navigation_history = self.navigation_history[-25:]

        # Cache navigation breadcrumbs
        breadcrumb_key = f"{self.config.key_prefix}:breadcrumbs:{self.current_session['session_id']}"
        try:
            await self.client.setex(
                breadcrumb_key,
                3600,  # 1 hour TTL
                json.dumps(self.navigation_history[-10:], default=str)  # Last 10 for breadcrumbs
            )
        except Exception as e:
            logger.error(f"Failed to cache navigation breadcrumbs: {e}")

    # Diagnostic and Error Caching

    async def cache_diagnostics(
        self,
        file_uri: str,
        diagnostics: List[Dict[str, Any]]
    ) -> bool:
        """Cache file diagnostics with ADHD-friendly filtering."""
        file_path = file_uri.replace("file://", "")
        cache_key = self._generate_cache_key("diagnostics", file_path)

        # ADHD optimization: categorize diagnostics by severity
        categorized = {
            "errors": [d for d in diagnostics if d.get("severity", 1) == 1],
            "warnings": [d for d in diagnostics if d.get("severity", 2) == 2],
            "info": [d for d in diagnostics if d.get("severity", 3) >= 3],
            "total_count": len(diagnostics)
        }

        diagnostic_data = {
            "diagnostics": diagnostics,
            "categorized": categorized,
            "file_path": file_path,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            await self.client.setex(
                cache_key,
                300,  # 5 minutes TTL for diagnostics
                json.dumps(diagnostic_data, default=str)
            )

            logger.debug(f"💾 Cached diagnostics for {Path(file_path).name}: {categorized['total_count']} issues")
            return True

        except Exception as e:
            logger.error(f"Failed to cache diagnostics: {e}")
            return False

    async def get_file_diagnostics(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get cached file diagnostics."""
        cache_key = self._generate_cache_key("diagnostics", file_path)
        return await self.get_navigation_result(cache_key)

    # Intelligent Prefetching

    async def prefetch_related_symbols(
        self,
        current_file: str,
        current_symbol: str,
        workspace_path: Path
    ) -> None:
        """Prefetch symbols for related files (ADHD context building)."""
        try:
            # Find related files based on imports, same directory, etc.
            related_files = await self._find_related_files(current_file, workspace_path)

            # Prefetch symbols for related files (low priority background task)
            prefetch_tasks = []
            for related_file in related_files[:5]:  # Limit to 5 to avoid overwhelming
                task = asyncio.create_task(
                    self._background_prefetch_symbols(related_file),
                    name=f"prefetch_symbols_{Path(related_file).name}"
                )
                prefetch_tasks.append(task)

            # Don't wait for completion, just start the tasks
            logger.debug(f"🔮 Started prefetching symbols for {len(related_files)} related files")

        except Exception as e:
            logger.error(f"Prefetch failed for {current_file}: {e}")

    async def _find_related_files(self, current_file: str, workspace_path: Path) -> List[str]:
        """Find files related to current file for prefetching."""
        related_files = []
        current_path = Path(current_file)

        try:
            # Same directory files
            if current_path.parent.exists():
                same_dir_files = [
                    str(f) for f in current_path.parent.glob(f"*{current_path.suffix}")
                    if f != current_path and f.is_file()
                ]
                related_files.extend(same_dir_files[:3])

            # Import analysis would go here for more intelligent related file detection
            # For now, simple heuristics

            return related_files

        except Exception as e:
            logger.error(f"Failed to find related files for {current_file}: {e}")
            return []

    async def _background_prefetch_symbols(self, file_path: str) -> None:
        """Background task to prefetch symbols for file."""
        try:
            # Check if already cached
            cache_key = self._generate_cache_key("symbols", file_path)
            if await self.client.exists(cache_key):
                return  # Already cached

            # This would integrate with the LSP wrapper to actually fetch symbols
            # For now, just mark as prefetch attempted
            prefetch_key = f"{cache_key}:prefetch_attempted"
            await self.client.setex(prefetch_key, 300, "true")

            logger.debug(f"🔮 Prefetch attempted for {Path(file_path).name}")

        except Exception as e:
            logger.error(f"Background prefetch failed for {file_path}: {e}")

    # Navigation History and Breadcrumbs

    async def add_navigation_breadcrumb(
        self,
        file_path: str,
        line: int,
        character: int,
        action: str,
        context: Dict[str, Any] = None
    ) -> None:
        """Add navigation breadcrumb for ADHD context preservation."""
        breadcrumb = {
            "file_path": file_path,
            "line": line,
            "character": character,
            "action": action,
            "context": context or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.current_session["session_id"]
        }

        # Add to local history
        self.navigation_history.append(breadcrumb)

        # ADHD optimization: keep breadcrumbs manageable
        if len(self.navigation_history) > 20:
            self.navigation_history = self.navigation_history[-15:]

        # Cache breadcrumb trail
        breadcrumb_key = f"{self.config.key_prefix}:breadcrumbs:{self.current_session['session_id']}"
        try:
            await self.client.setex(
                breadcrumb_key,
                3600,  # 1 hour
                json.dumps(self.navigation_history, default=str)
            )

            logger.debug(f"🍞 Navigation breadcrumb added: {action} in {Path(file_path).name}:{line}")

        except Exception as e:
            logger.error(f"Failed to cache breadcrumb: {e}")

    async def get_navigation_breadcrumbs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent navigation breadcrumbs for ADHD context."""
        breadcrumb_key = f"{self.config.key_prefix}:breadcrumbs:{self.current_session['session_id']}"

        try:
            cached_breadcrumbs = await self.client.get(breadcrumb_key)
            if cached_breadcrumbs:
                breadcrumbs = json.loads(cached_breadcrumbs)
                return breadcrumbs[-limit:] if breadcrumbs else []

            # Return local breadcrumbs if cache miss
            return self.navigation_history[-limit:]

        except Exception as e:
            logger.error(f"Failed to get navigation breadcrumbs: {e}")
            return self.navigation_history[-limit:]

    # Workspace State Management

    async def save_workspace_navigation_state(
        self,
        workspace_path: str,
        state: Dict[str, Any]
    ) -> bool:
        """Save workspace navigation state for session persistence."""
        workspace_key = f"{self.config.key_prefix}:workspace:{hashlib.sha256(workspace_path.encode()).hexdigest()[:12]}"

        workspace_state = {
            **state,
            "workspace_path": workspace_path,
            "session_id": self.current_session["session_id"],
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "navigation_history": self.navigation_history[-5:]  # Recent navigation for context
        }

        try:
            await self.client.setex(
                workspace_key,
                86400,  # 24 hours
                json.dumps(workspace_state, default=str)
            )

            logger.info(f"💾 Workspace navigation state saved for {Path(workspace_path).name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save workspace state: {e}")
            return False

    async def restore_workspace_navigation_state(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        """Restore workspace navigation state for ADHD context continuity."""
        workspace_key = f"{self.config.key_prefix}:workspace:{hashlib.sha256(workspace_path.encode()).hexdigest()[:12]}"

        try:
            cached_state = await self.client.get(workspace_key)
            if cached_state:
                state_data = json.loads(cached_state)

                # Restore navigation history for context
                restored_history = state_data.get("navigation_history", [])
                if restored_history:
                    self.navigation_history.extend(restored_history)

                logger.info(f"📂 Workspace navigation state restored for {Path(workspace_path).name}")
                return state_data

            return None

        except Exception as e:
            logger.error(f"Failed to restore workspace state: {e}")
            return None

    # Performance and Monitoring

    async def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            # Get memory usage and key counts
            info = await self.client.info("memory")
            memory_usage = info.get("used_memory_human", "unknown")

            # Count keys by type
            key_pattern = f"{self.config.key_prefix}:*"
            keys = await self.client.keys(key_pattern)

            key_counts = {}
            for key in keys:
                parts = key.split(":")
                if len(parts) >= 4:
                    key_type = parts[3]  # symbols, definition, etc.
                    key_counts[key_type] = key_counts.get(key_type, 0) + 1

            return {
                "total_keys": len(keys),
                "memory_usage": memory_usage,
                "key_counts": key_counts,
                "navigation_history_size": len(self.navigation_history),
                "session_id": self.current_session["session_id"]
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Health check for navigation cache."""
        try:
            if not self.client:
                return {"status": "🔴 Not initialized"}

            # Test connectivity
            start_time = datetime.now()
            await self.client.ping()
            latency = (datetime.now() - start_time).total_seconds() * 1000

            cache_stats = await self._get_cache_stats()

            # Determine health status
            if latency < 100:
                status = "🚀 Excellent"
            elif latency < 500:
                status = "✅ Good"
            else:
                status = "⚠️ Slow"

            return {
                "status": status,
                "latency_ms": round(latency, 2),
                "cache_stats": cache_stats,
                "initialized": self._initialized
            }

        except Exception as e:
            logger.error(f"Navigation cache health check failed: {e}")
            return {
                "status": "🔴 Unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }

    async def close(self) -> None:
        """Close navigation cache connection."""
        if self.client:
            await self.client.close()
            self._initialized = False
            logger.info("🔌 Navigation cache connections closed")

    # Cache Maintenance

    async def cleanup_stale_entries(self, max_age_hours: int = 24) -> int:
        """Clean up stale cache entries to prevent memory bloat."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            # This is a simplified cleanup - in production, would use more sophisticated eviction
            pattern = f"{self.config.key_prefix}:*"
            keys = await self.client.keys(pattern)

            cleaned_count = 0
            for key in keys:
                try:
                    # Check if key has data with timestamp
                    data = await self.client.get(key)
                    if data:
                        parsed_data = json.loads(data)
                        cached_at = parsed_data.get("cached_at")
                        if cached_at:
                            cached_time = datetime.fromisoformat(cached_at)
                            if cached_time < cutoff_time:
                                await self.client.delete(key)
                                cleaned_count += 1
                except (json.JSONDecodeError, ValueError):
                    # Invalid data, remove it
                    await self.client.delete(key)
                    cleaned_count += 1

            logger.info(f"🧹 Cleaned up {cleaned_count} stale navigation cache entries")
            return cleaned_count

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            return 0