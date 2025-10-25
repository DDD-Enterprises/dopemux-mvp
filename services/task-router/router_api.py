"""
F-NEW-9 Week 2: Task Router API

HTTP endpoints for intelligent task suggestions.
Integrates F-NEW-6 (session intelligence) + F-NEW-3 (complexity) + matching engine.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

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

            if not user_id:
                return web.json_response({'error': 'user_id required'}, status=400)

            start_time = datetime.now()

            # Step 1: Get current cognitive state from F-NEW-6
            cognitive_state = await self._get_cognitive_state(user_id)

            # Step 2: Get TODO tasks from ConPort
            todo_tasks = await self._get_todo_tasks(user_id)

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

            if not user_id or not task_id:
                return web.json_response(
                    {'error': 'user_id and task_id required'},
                    status=400
                )

            # Get cognitive state
            cognitive_state = await self._get_cognitive_state(user_id)

            # Get task details
            task = await self._get_task_by_id(user_id, task_id)
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
                todo_tasks = await self._get_todo_tasks(user_id)
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

            if not user_id:
                return web.json_response({'error': 'user_id required'}, status=400)

            # Get tasks
            todo_tasks = await self._get_todo_tasks(user_id)
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
            # Query ADHD Engine directly for now
            # TODO: Use Serena MCP when available
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

    async def _get_todo_tasks(self, user_id: str) -> List[Task]:
        """Get TODO tasks from ConPort."""
        try:
            # Query ConPort for IN_PROGRESS and TODO tasks
            async with ClientSession() as session:
                # Using workspace_id for now (will support user_id in Phase 2)
                workspace_id = "/Users/hue/code/dopemux-mvp"  # Placeholder

                url = f"{self.conport_url}/api/progress?workspace_id={workspace_id}&status=TODO"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        progress_entries = data.get('progress_entries', [])

                        # Convert to Task objects
                        tasks = []
                        for entry in progress_entries:
                            task = Task(
                                task_id=entry.get('id', ''),
                                title=entry.get('description', ''),
                                description=entry.get('description', ''),
                                complexity=0.5,  # Will be enriched
                                estimated_minutes=entry.get('estimated_hours', 1) * 60,
                                priority=entry.get('priority', 'medium'),
                                task_type=self._infer_task_type(entry.get('description', '')),
                                requires_focus=False  # Will be determined by complexity
                            )
                            tasks.append(task)

                        return tasks
        except Exception as e:
            logger.warning(f"Failed to get TODO tasks: {e}")

        return []

    async def _get_task_by_id(self, user_id: str, task_id: str) -> Optional[Task]:
        """Get specific task by ID."""
        tasks = await self._get_todo_tasks(user_id)
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None

    async def _enrich_tasks_with_complexity(self, tasks: List[Task]) -> List[Task]:
        """Enrich tasks with F-NEW-3 complexity scores."""
        # For now, use simple heuristics
        # TODO: Integrate with F-NEW-3 unified complexity when available

        for task in tasks:
            # Infer complexity from description keywords
            desc_lower = task.description.lower()

            if any(word in desc_lower for word in ['refactor', 'architecture', 'redesign', 'complex']):
                task.complexity = 0.8
                task.requires_focus = True
            elif any(word in desc_lower for word in ['implement', 'feature', 'integration']):
                task.complexity = 0.5
                task.requires_focus = False
            elif any(word in desc_lower for word in ['fix', 'update', 'document', 'readme']):
                task.complexity = 0.2
                task.requires_focus = False
            else:
                task.complexity = 0.4  # Default moderate

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
