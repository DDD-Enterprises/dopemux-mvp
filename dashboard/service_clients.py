"""
Service-Specific API Clients
High-level clients for each backend service with domain-specific methods
"""

import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from dashboard.api_client import APIClient, APIConfig, CacheStrategy

logger = logging.getLogger(__name__)


class ADHDEngineClient(APIClient):
    """
    Client for ADHD Engine API
    
    Provides access to:
    - Energy level tracking
    - Attention state monitoring
    - Task suitability assessment
    - Break recommendations
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(APIConfig(
            base_url=base_url,
            cache_strategy=CacheStrategy.SHORT,  # 5s for real-time state
            timeout=3.0
        ))
    
    async def get_energy_level(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get current energy level
        
        Returns:
            {
                "energy_level": "LOW" | "MEDIUM" | "HIGH" | "PEAK",
                "confidence": 0.0-1.0,
                "factors": List[str],
                "recommendations": List[str],
                "last_updated": ISO8601 timestamp
            }
        """
        return await self.get(
            f"/api/v1/energy-level/{user_id}",
            cache_key=f"energy_{user_id}",
            fallback_data={
                "energy_level": "MEDIUM",
                "confidence": 0.5,
                "factors": ["Service unavailable - using default"],
                "recommendations": ["Ensure ADHD Engine is running"],
                "last_updated": datetime.now().isoformat()
            }
        ) or {}
    
    async def get_attention_state(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get current attention state
        
        Returns:
            {
                "state": "FOCUSED" | "SCATTERED" | "HYPERFOCUS" | "DISTRACTED",
                "duration_minutes": int,
                "interruptions_count": int,
                "quality_score": 0.0-1.0,
                "stability": "HIGH" | "MEDIUM" | "LOW"
            }
        """
        return await self.get(
            f"/api/v1/attention-state/{user_id}",
            cache_key=f"attention_{user_id}",
            fallback_data={
                "state": "FOCUSED",
                "duration_minutes": 0,
                "interruptions_count": 0,
                "quality_score": 0.5,
                "stability": "MEDIUM"
            }
        ) or {}
    
    async def assess_task(
        self,
        user_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess task suitability for current state
        
        Args:
            user_id: User identifier
            task_data: {
                "id": str,
                "title": str,
                "complexity": 0.0-1.0,
                "estimated_duration_minutes": int
            }
        
        Returns:
            {
                "is_suitable": bool,
                "suitability_score": 0.0-1.0,
                "match_breakdown": {...},
                "accommodations": List[Dict],
                "warnings": List[str]
            }
        """
        result = await self.post(
            "/api/v1/assess-task",
            json_data={
                "user_id": user_id,
                "task_data": task_data
            },
            fallback_data={
                "is_suitable": True,
                "suitability_score": 0.5,
                "match_breakdown": {
                    "energy_match": 0.5,
                    "attention_match": 0.5,
                    "time_match": 0.5
                },
                "accommodations": [],
                "warnings": ["Assessment service unavailable"]
            }
        )
        
        return result or {}
    
    async def recommend_break(
        self,
        user_id: str,
        current_duration: int,
        cognitive_load: float
    ) -> Dict[str, Any]:
        """
        Get break recommendation
        
        Returns:
            {
                "should_break": bool,
                "urgency": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
                "recommended_duration_minutes": int,
                "break_type": "MICRO" | "SHORT" | "LONG" | "WALK",
                "activities": List[str],
                "reasons": List[str]
            }
        """
        result = await self.post(
            "/api/v1/recommend-break",
            json_data={
                "user_id": user_id,
                "session_context": {
                    "current_duration_minutes": current_duration,
                    "cognitive_load": cognitive_load
                }
            },
            fallback_data={
                "should_break": False,
                "urgency": "LOW",
                "recommended_duration_minutes": 5,
                "break_type": "MICRO",
                "activities": ["Take a brief pause"],
                "reasons": []
            }
        )
        
        return result or {}


class DockerServiceClient:
    """
    Client for Docker service health and logs
    Uses subprocess for docker commands
    """
    
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get Docker service status
        
        Returns:
            {
                "service": str,
                "status": str (e.g., "Up 3 hours"),
                "state": "running" | "exited" | "unknown",
                "is_healthy": bool
            }
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'ps',
                '--filter', f'name={service_name}',
                '--format', '{{.Status}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                status = stdout.decode().strip()
                
                if status:
                    is_running = status.lower().startswith('up')
                    return {
                        "service": service_name,
                        "status": status,
                        "state": "running" if is_running else "exited",
                        "is_healthy": is_running
                    }
                else:
                    # Container not found
                    return {
                        "service": service_name,
                        "status": "Not found",
                        "state": "not_found",
                        "is_healthy": False
                    }
            else:
                logger.error(f"Docker ps failed: {stderr.decode()}")
        except FileNotFoundError:
            logger.error("Docker command not found - is Docker installed?")
        except Exception as e:
            logger.error(f"Failed to get service status: {e}")
        
        return {
            "service": service_name,
            "status": "Unknown",
            "state": "unknown",
            "is_healthy": False
        }
    
    async def get_recent_logs(
        self,
        service_name: str,
        lines: int = 100
    ) -> List[str]:
        """
        Get recent logs from Docker service
        
        Returns:
            List of log lines (newest last)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                'docker', 'logs',
                '--tail', str(lines),
                service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await proc.communicate()
            
            if proc.returncode == 0:
                log_text = stdout.decode()
                return [line for line in log_text.split('\n') if line.strip()]
            else:
                logger.warning(f"Failed to get logs for {service_name}")
        except FileNotFoundError:
            logger.error("Docker command not found")
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
        
        return [f"Unable to fetch logs for {service_name}"]
    
    async def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all known services
        
        Returns:
            Dict mapping service name to status info
        """
        services = [
            "adhd_engine",
            "conport",
            "serena",
            "prometheus",
            "redis",
            "postgres"
        ]
        
        results = await asyncio.gather(*[
            self.get_service_status(svc)
            for svc in services
        ])
        
        return {svc: status for svc, status in zip(services, results)}


class ConPortClient:
    """
    Client for ConPort decision database
    
    Currently uses direct database access.
    TODO: Migrate to HTTP API when bridge is ready
    """
    
    def __init__(self):
        # Placeholder for database connection
        # In production, this would use asyncpg
        self.db = None
    
    async def get_recent_decisions(
        self,
        user_id: str = "default",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent decisions from database

        Returns:
            List of decision objects with metadata
        """
        # Use ConPort HTTP API
        try:
            import httpx
            conport_url = "http://localhost:5455/conport/get_decisions"
            workspace_id = "/Users/hue/code/dopemux-mvp"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{conport_url}?workspace_id={workspace_id}&limit={limit}")
                if response.status_code == 200:
                    decisions_data = response.json()
                    decisions = decisions_data.get("decisions", [])

                    # Format for dashboard consumption
                    formatted_decisions = []
                    for decision in decisions[:limit]:
                        formatted_decisions.append({
                            "id": decision.get("id", f"dec_{len(formatted_decisions)}"),
                            "type": "ARCHITECTURAL",  # Default type
                            "summary": decision.get("summary", "Decision summary"),
                            "outcome": "SUCCESSFUL",  # Assume successful
                            "created_at": decision.get("timestamp", datetime.now().isoformat()),
                            "tags": decision.get("tags", [])
                        })
                    return formatted_decisions
        except Exception as e:
            logger.warning(f"ConPort decision fetch failed: {e}")

        # Fallback to mock data
        logger.warning("ConPort HTTP API not available - using mock data")
        return [
            {
                "id": f"dec_{i}",
                "type": "TASK_SELECTION",
                "summary": f"Mock decision {i}",
                "outcome": "SUCCESSFUL",
                "created_at": datetime.now().isoformat(),
                "tags": ["mock"]
            }
            for i in range(min(limit, 5))
        ]
    
    async def get_current_context(
        self,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Get current user context

        Returns:
            {
                "current_project": str,
                "active_tasks": List[str],
                "session_duration_minutes": int,
                "context_switches_count": int
            }
        """
        # Use ConPort active context
        try:
            import httpx
            conport_url = "http://localhost:5455/conport/get_active_context"
            workspace_id = "/Users/hue/code/dopemux-mvp"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{conport_url}?workspace_id={workspace_id}")
                if response.status_code == 200:
                    context_data = response.json()
                    active_context = context_data.get("active_context", {})

                    # Extract relevant information
                    current_focus = active_context.get("current_focus", "")
                    session_duration = active_context.get("session_duration_minutes", 45)

                    # Get active tasks from progress entries
                    progress_response = await client.get(f"http://localhost:5455/conport/get_progress?workspace_id={workspace_id}&status_filter=IN_PROGRESS")
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        active_tasks = [
                            entry.get("description", "")[:50] + "..." if len(entry.get("description", "")) > 50 else entry.get("description", "")
                            for entry in progress_data.get("progress_entries", [])[:5]  # Limit to 5 tasks
                        ]
                    else:
                        active_tasks = ["task_1", "task_2"]

                    return {
                        "current_project": "dopemux-mvp",
                        "active_tasks": active_tasks,
                        "session_duration_minutes": session_duration,
                        "context_switches_count": active_context.get("context_switches_count", 7)
                    }
        except Exception as e:
            logger.warning(f"ConPort context fetch failed: {e}")

        # Fallback to mock data
        logger.warning("ConPort HTTP API not available - using mock data")
        return {
            "current_project": "dopemux-mvp",
            "active_tasks": ["task_1", "task_2"],
            "session_duration_minutes": 45,
            "context_switches_count": 7
        }


class DataPrefetcher:
    """
    Background prefetcher for common data
    Reduces modal load times by keeping hot data in cache
    """
    
    def __init__(self):
        self.adhd_client = ADHDEngineClient()
        self.docker_client = DockerServiceClient()
        
        self.prefetched_data = {}
        self.prefetch_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """Start background prefetching"""
        if not self._running:
            self._running = True
            self.prefetch_task = asyncio.create_task(self._prefetch_loop())
            logger.info("Data prefetcher started")
    
    def stop(self):
        """Stop background prefetching"""
        self._running = False
        if self.prefetch_task:
            self.prefetch_task.cancel()
            logger.info("Data prefetcher stopped")
    
    async def _prefetch_loop(self):
        """Continuously prefetch likely-needed data"""
        while self._running:
            try:
                await asyncio.gather(
                    self._prefetch_adhd_state(),
                    self._prefetch_service_status(),
                    return_exceptions=True
                )
            except Exception as e:
                logger.error(f"Prefetch error: {e}")
            
            await asyncio.sleep(10)  # Prefetch every 10s
    
    async def _prefetch_adhd_state(self):
        """Prefetch ADHD state for task modal"""
        try:
            energy, attention = await asyncio.gather(
                self.adhd_client.get_energy_level("default"),
                self.adhd_client.get_attention_state("default")
            )
            
            self.prefetched_data['adhd_state'] = {
                'energy': energy,
                'attention': attention,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to prefetch ADHD state: {e}")
    
    async def _prefetch_service_status(self):
        """Prefetch service status for logs modal"""
        try:
            statuses = await self.docker_client.get_all_services_status()
            
            self.prefetched_data['service_status'] = {
                'data': statuses,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to prefetch service status: {e}")
    
    def get_prefetched(
        self,
        key: str,
        max_age_seconds: int = 30
    ) -> Optional[Any]:
        """Get prefetched data if fresh enough"""
        if key not in self.prefetched_data:
            return None
        
        entry = self.prefetched_data[key]
        age = (datetime.now() - entry['timestamp']).total_seconds()
        
        if age < max_age_seconds:
            return entry.get('data') or entry
        
        return None
