"""
Task Orchestrator Client for ADHD Engine

Enables ADHD Engine to request task decomposition from Task Orchestrator.
Task Orchestrator handles Pal planner calls, ConPort persistence, and Leantime sync.
"""
from typing import Dict, Any, Optional, List
import aiohttp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskOrchestratorClient:
    """
    Client for ADHD Engine to communicate with Task Orchestrator.
    
    Task Orchestrator is the coordination hub that:
    - Calls Pal planner for AI-powered decomposition
    - Persists to ConPort via DopeconBridge
    - Syncs to Leantime (creates child tickets)
    - Returns structured breakdown
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize Task Orchestrator client.
        
        Args:
            base_url: Task Orchestrator API URL (default: localhost:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def request_decomposition(
        self,
        task_id: str,
        adhd_context: Dict[str, Any],
        method: str = "pal",
        max_subtasks: int = 7,
        target_duration_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Request task decomposition from Task Orchestrator.
        
        Task Orchestrator will:
        1. Call Pal planner for AI breakdown (or use pattern fallback)
        2. Convert to OrchestrationTask objects
        3. Persist to ConPort (parent BLOCKED, subtasks TODO, DECOMPOSED_INTO links)
        4. Sync to Leantime (create child tickets for team visibility)
        5. Return structured breakdown
        
        Args:
            task_id: Task ID to decompose
            adhd_context: Current ADHD state (energy, attention, cognitive load)
            method: "pal" (AI) or "pattern" (rule-based fallback)
            max_subtasks: Maximum number of subtasks (default 7)
            target_duration_minutes: Target duration per subtask (default 15min)
        
        Returns:
            {
                "subtask_ids": ["T-124", "T-125", ...],
                "subtasks": [...],  # Full OrchestrationTask objects
                "total_estimated_minutes": 120,
                "break_points": ["after T-125", "after T-127"],
                "schedule": {...},  # Energy-aware schedule
                "leantime_synced": true,  # Whether synced to Leantime
                "conport_persisted": true  # Whether saved to ConPort
            }
        
        Raises:
            aiohttp.ClientError: If Task Orchestrator unavailable
            ValueError: If decomposition fails
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        try:
            logger.info(f"Requesting decomposition for task {task_id} via {method} method")
            
            async with self.session.post(
                f"{self.base_url}/api/decompose",
                json={
                    "task_id": task_id,
                    "adhd_context": adhd_context,
                    "method": method,
                    "max_subtasks": max_subtasks,
                    "target_duration_minutes": target_duration_minutes,
                    "timestamp": datetime.now().isoformat()
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(
                        f"Decomposition successful: {len(result.get('subtask_ids', []))} subtasks created"
                    )
                    return result
                elif resp.status == 404:
                    error_detail = await resp.text()
                    logger.error(f"Task not found: {error_detail}")
                    raise ValueError(f"Task {task_id} not found in Task Orchestrator")
                elif resp.status == 500:
                    error_detail = await resp.text()
                    logger.error(f"Decomposition failed: {error_detail}")
                    raise ValueError(f"Task Orchestrator decomposition failed: {error_detail}")
                else:
                    error_detail = await resp.text()
                    logger.error(f"Unexpected response {resp.status}: {error_detail}")
                    raise ValueError(f"Decomposition request failed: {error_detail}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Task Orchestrator connection error: {e}")
            raise
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task details from Task Orchestrator.
        
        Args:
            task_id: Task ID to fetch
        
        Returns:
            Task data or None if not found
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with context manager.")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/tasks/{task_id}"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    logger.warning(f"Task {task_id} not found in Task Orchestrator")
                    return None
                else:
                    logger.error(f"Failed to fetch task {task_id}: {resp.status}")
                    return None
        
        except aiohttp.ClientError as e:
            logger.error(f"Task Orchestrator connection error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Task Orchestrator is available.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            )
        
        try:
            async with self.session.get(f"{self.base_url}/health") as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Task Orchestrator health check failed: {e}")
            return False
