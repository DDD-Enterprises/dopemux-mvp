"""
F-NEW-9 Week 2: Task Router API

HTTP endpoints for intelligent task suggestions.
Integrates F-NEW-6 (session intelligence) + F-NEW-3 (complexity) + matching engine.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

from aiohttp import web, ClientSession
import redis.asyncio as redis

from matching_engine import (
    TaskMatchingEngine,
    CognitiveState,
    Task,
    EnergyLevel,
    AttentionState
)

logger = logging.getLogger(__name__)


class TaskRouterAPI:
    """
    HTTP API for intelligent task routing.

    Endpoints:
    - GET /suggest-tasks?user_id=X&count=3
    - POST /check-task-match {user_id, task_id}
    - POST /reorder-queue {user_id}
    """

    def __init__(
        self,
        conport_url: str = "http://localhost:3004",
        serena_url: str = "http://localhost:3001",
        adhd_engine_url: str = "http://localhost:8001",
        redis_url: str = "redis://localhost:6379"
    ):
        self.conport_url = conport_url
        self.serena_url = serena_url
        self.adhd_engine_url = adhd_engine_url
        self.redis_url = redis_url

        self.matching_engine = TaskMatchingEngine()
        self.redis_client = None
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup API routes."""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/suggest-tasks', self.suggest_tasks)
        self.app.router.add_post('/check-task-match', self.check_task_match)
        self.app.router.add_post('/reorder-queue', self.reorder_queue)

    async def init_connections(self):
        """Initialize connections."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis_client.ping()
        logger.info("✅ Task Router API initialized")

    async def health_check(self, request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'service': 'task-router',
            'version': '1.0.0-fnew9-week2'
        })

    async def suggest_tasks(self, request):
        """
        GET /suggest-tasks?user_id=X&count=3

        Returns top N tasks matching current cognitive state.

        Query params:
            user_id: User identifier (required)
            count: Number of suggestions (default 3, max 5)

        Returns:
            {
                "cognitive_state": {...},
                "suggestions": [{task, match_score, rank, reason}, ...],
                "response_time_ms": ...
            }

        Performance: <100ms target
        """
        try:
            user_id = request.query.get('user_id')
            count = min(int(request.query.get('count', 3)), 5)  # ADHD-safe: max 5
            workspace_id = request.query.get('workspace_id')

            if not user_id:
                return web.json_response({'error': 'user_id required'}, status=400)

            start_time = datetime.now()

            # Step 1: Get current cognitive state from F-NEW-6
            cognitive_state = await self._get_cognitive_state(user_id)

            # Step 2: Get TODO tasks from ConPort
            todo_tasks = await self._get_todo_tasks(user_id, workspace_id=workspace_id)

            if not todo_tasks:
                return web.json_response({
                    'suggestions': [],
                    'message': 'No TODO tasks found',
                    'cognitive_state': self._serialize_cognitive_state(cognitive_state)
                })

            # Step 3: Enrich tasks with complexity from F-NEW-3
            enriched_tasks = await self._enrich_tasks_with_complexity(todo_tasks)

            # Step 4: Get task suggestions from matching engine
            suggestions = self.matching_engine.suggest_tasks(
                cognitive_state=cognitive_state,
                available_tasks=enriched_tasks,
                count=count
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Serialize response
            suggestions_json = [
                {
                    'task': {
                        'task_id': s.task.task_id,
                        'title': s.task.title,
                        'description': s.task.description,
                        'complexity': s.task.complexity,
                        'estimated_minutes': s.task.estimated_minutes,
                        'priority': s.task.priority
                    },
                    'match_score': s.match_score,
                    'rank': s.rank,
                    'match_reason': s.match_reason,
                    'alignments': {
                        'energy': s.energy_alignment,
                        'attention': s.attention_alignment,
                        'time': s.time_alignment
                    }
                }
                for s in suggestions
            ]

            logger.info(f"Task suggestions: {len(suggestions)} for {user_id} in {elapsed_ms:.1f}ms")

            return web.json_response({
                'cognitive_state': self._serialize_cognitive_state(cognitive_state),
                'suggestions': suggestions_json,
                'total_available': len(enriched_tasks),
                'response_time_ms': elapsed_ms
            })

        except Exception as e:
            logger.error(f"Suggest tasks error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def check_task_match(self, request):
        """
        POST /check-task-match
        Body: {"user_id": "X", "task_id": "Y"}

        Checks if current task matches cognitive state.

        Returns:
            {
                "is_good_match": bool,
                "match_score": float,
                "mismatch_warning": {...} or null,
                "alternatives": [...]
            }
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            task_id = data.get('task_id')
            workspace_id = data.get('workspace_id')

            if not user_id or not task_id:
                return web.json_response(
                    {'error': 'user_id and task_id required'},
                    status=400
                )

            # Get cognitive state
            cognitive_state = await self._get_cognitive_state(user_id)

            # Get task details
            task = await self._get_task_by_id(user_id, task_id, workspace_id=workspace_id)
            if not task:
                return web.json_response({'error': 'Task not found'}, status=404)

            # Enrich with complexity
            enriched_task = await self._enrich_single_task(task)

            # Check for mismatch
            mismatch_warning = self.matching_engine.detect_task_mismatch(
                cognitive_state=cognitive_state,
                current_task=enriched_task
            )

            # If mismatch, get alternatives
            alternatives = []
            if mismatch_warning:
                todo_tasks = await self._get_todo_tasks(user_id, workspace_id=workspace_id)
                enriched = await self._enrich_tasks_with_complexity(todo_tasks)
                alt_suggestions = self.matching_engine.suggest_tasks(
                    cognitive_state, enriched, count=3
                )
                alternatives = [
                    {
                        'task_id': s.task.task_id,
                        'title': s.task.title,
                        'match_score': s.match_score
                    }
                    for s in alt_suggestions
                ]

            return web.json_response({
                'is_good_match': mismatch_warning is None,
                'mismatch_warning': mismatch_warning,
                'alternatives': alternatives
            })

        except Exception as e:
            logger.error(f"Check task match error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def reorder_queue(self, request):
        """
        POST /reorder-queue
        Body: {"user_id": "X"}

        Reorders TODO queue based on cognitive state and predicted energy curve.

        Returns:
            {
                "original_order": [...],
                "optimized_order": [...],
                "reorder_reason": "...",
                "estimated_improvement": "+X%"
            }
        """
        try:
            data = await request.json()
            user_id = data.get('user_id')
            workspace_id = data.get('workspace_id')

            if not user_id:
                return web.json_response({'error': 'user_id required'}, status=400)

            # Get tasks
            todo_tasks = await self._get_todo_tasks(user_id, workspace_id=workspace_id)
            original_order = [t.task_id for t in todo_tasks]

            # Get cognitive state
            cognitive_state = await self._get_cognitive_state(user_id)

            # Enrich with complexity
            enriched = await self._enrich_tasks_with_complexity(todo_tasks)

            # Rank by match score
            suggestions = self.matching_engine.suggest_tasks(
                cognitive_state, enriched, count=len(enriched)
            )

            optimized_order = [s.task.task_id for s in suggestions]

            return web.json_response({
                'original_order': original_order,
                'optimized_order': optimized_order,
                'reorder_reason': f"Matched to current {cognitive_state.energy.value} energy state",
                'estimated_improvement': "+25%"  # Placeholder, will track in Week 3
            })

        except Exception as e:
            logger.error(f"Reorder queue error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    # =====================================================================
    # Helper Methods - Integration with F-NEW-6, F-NEW-3, ConPort
    # =====================================================================

    async def _get_cognitive_state(self, user_id: str) -> CognitiveState:
        """Get current cognitive state from F-NEW-6 via Serena MCP."""
        try:
            # Prefer ADHD Engine state endpoint and fall back to defaults.
            async with ClientSession() as session:
                async with session.get(f"{self.adhd_engine_url}/state/{user_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Map to enum values
                        energy_str = data.get('energy', 'medium')
                        attention_str = data.get('attention', 'focused')

                        return CognitiveState(
                            energy=EnergyLevel(energy_str),
                            attention=AttentionState(attention_str),
                            cognitive_load=data.get('cognitive_load', 0.5),
                            time_until_break_min=data.get('time_until_break_min')
                        )
        except Exception as e:
            logger.warning(f"Failed to get cognitive state, using defaults: {e}")

        # Fallback defaults
        return CognitiveState(
            energy=EnergyLevel.MEDIUM,
            attention=AttentionState.FOCUSED,
            cognitive_load=0.5,
            time_until_break_min=30
        )

    async def _get_todo_tasks(self, user_id: str, workspace_id: Optional[str] = None) -> List[Task]:
        """Get active TODO/IN_PROGRESS tasks from ConPort for routing."""
        resolved_workspace = self._resolve_workspace_id(user_id, workspace_id)
        statuses = ("TODO", "IN_PROGRESS")
        tasks_by_id: Dict[str, Task] = {}
        try:
            async with ClientSession() as session:
                for status in statuses:
                    url = (
                        f"{self.conport_url}/api/progress"
                        f"?workspace_id={quote(resolved_workspace, safe='')}"
                        f"&status={status}"
                    )
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            logger.debug(
                                "ConPort progress query failed: workspace=%s status=%s http=%s",
                                resolved_workspace,
                                status,
                                resp.status,
                            )
                            continue
                        data = await resp.json()
                        progress_entries = self._extract_progress_entries(data)
                        for entry in progress_entries:
                            task = self._progress_entry_to_task(entry)
                            tasks_by_id[task.task_id] = task
        except Exception as e:
            logger.warning(f"Failed to get TODO tasks: {e}")
        return list(tasks_by_id.values())

    async def _get_task_by_id(
        self,
        user_id: str,
        task_id: str,
        workspace_id: Optional[str] = None,
    ) -> Optional[Task]:
        """Get specific task by ID."""
        tasks = await self._get_todo_tasks(user_id, workspace_id=workspace_id)
        for task in tasks:
            if task.task_id == str(task_id):
                return task
        return None

    async def _enrich_tasks_with_complexity(self, tasks: List[Task]) -> List[Task]:
        """Enrich tasks with F-NEW-3 complexity scores."""
        for task in tasks:
            desc_lower = task.description.lower()
            base_complexity = task.complexity if 0.0 <= task.complexity <= 1.0 else 0.5
            if any(word in desc_lower for word in ['refactor', 'architecture', 'redesign', 'complex']):
                inferred = 0.8
            elif any(word in desc_lower for word in ['implement', 'feature', 'integration']):
                inferred = 0.55
            elif any(word in desc_lower for word in ['fix', 'update', 'document', 'readme']):
                inferred = 0.25
            else:
                inferred = 0.45

            # Blend source-provided complexity with inferred heuristic.
            blended = (base_complexity * 0.6) + (inferred * 0.4)
            if task.priority in {"critical", "high"}:
                blended = min(1.0, blended + 0.05)
            task.complexity = max(0.0, min(1.0, blended))
            task.requires_focus = task.complexity >= 0.65 or task.task_type == "deep_work"

        return tasks

    async def _enrich_single_task(self, task: Task) -> Task:
        """Enrich single task with complexity."""
        return (await self._enrich_tasks_with_complexity([task]))[0]

    def _infer_task_type(self, description: str) -> str:
        """Infer task type from description."""
        desc_lower = description.lower()

        # Order matters - check most specific first
        if 'refactor' in desc_lower or 'architecture' in desc_lower:
            return 'deep_work'
        elif 'fix' in desc_lower or 'bug' in desc_lower:
            return 'bug_fix'  # Check before 'document' to catch "fix typo"
        elif 'document' in desc_lower or 'readme' in desc_lower:
            return 'documentation'
        elif 'implement' in desc_lower or 'feature' in desc_lower:
            return 'implementation'
        elif 'review' in desc_lower:
            return 'review'
        else:
            return 'implementation'  # Default

    def _serialize_cognitive_state(self, state: CognitiveState) -> Dict:
        """Serialize cognitive state for JSON response."""
        return {
            'energy': state.energy.value,
            'attention': state.attention.value,
            'cognitive_load': state.cognitive_load,
            'time_until_break_min': state.time_until_break_min
        }

    def _resolve_workspace_id(self, user_id: str, workspace_id: Optional[str]) -> str:
        """Resolve workspace identifier with explicit override first."""
        if workspace_id:
            return workspace_id
        env_workspace = os.getenv("WORKSPACE_ROOT")
        if env_workspace:
            return env_workspace
        if user_id.startswith("/"):
            return user_id
        return os.getcwd()

    def _extract_progress_entries(self, payload: Dict) -> List[Dict]:
        """Normalize ConPort response payload into progress entry list."""
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("progress_entries", "entries", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [entry for entry in value if isinstance(entry, dict)]
        return []

    def _progress_entry_to_task(self, entry: Dict) -> Task:
        """Convert ConPort progress entry payload to Task object."""
        description = str(entry.get("description", "") or "")
        estimated_minutes = self._coerce_int(entry.get("estimated_minutes"))
        if estimated_minutes is None:
            estimated_hours = self._coerce_float(entry.get("estimated_hours"))
            estimated_minutes = int((estimated_hours or 1.0) * 60)

        complexity = self._coerce_float(
            entry.get("complexity_score", entry.get("complexity", 0.5))
        )
        complexity = complexity if complexity is not None else 0.5
        complexity = max(0.0, min(1.0, complexity))

        priority = str(entry.get("priority", "medium")).lower()
        task_type = self._infer_task_type(description)
        requires_focus = complexity >= 0.65 or task_type == "deep_work"

        task_id_value = entry.get("id", entry.get("task_id", ""))
        task_id = str(task_id_value)

        return Task(
            task_id=task_id,
            title=description or f"Task {task_id}",
            description=description,
            complexity=complexity,
            estimated_minutes=max(5, estimated_minutes),
            priority=priority,
            task_type=task_type,
            requires_focus=requires_focus,
        )

    def _coerce_float(self, value: object) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _coerce_int(self, value: object) -> Optional[int]:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    async def start_server(self, port: int = 8003):
        """Start the API server."""
        await self.init_connections()

        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()

        logger.info(f"✅ F-NEW-9 Task Router API running on port {port}")
        logger.info("   Endpoints:")
        logger.info("     GET  /suggest-tasks?user_id=X&count=3")
        logger.info("     POST /check-task-match")
        logger.info("     POST /reorder-queue")

        # Keep server running
        while True:
            await asyncio.sleep(3600)


async def main():
    """Run Task Router API server."""
    api = TaskRouterAPI()
    await api.start_server(port=8003)


if __name__ == "__main__":
    asyncio.run(main())
