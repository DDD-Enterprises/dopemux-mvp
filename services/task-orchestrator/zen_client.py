"""Zen MCP client for Task Orchestrator complex task planning."""

from typing import Dict, Any, List, Optional
import sys
import os

# Try to import the genetic_agent ZenClient, fall back to mock if not available
try:
    # Add the genetic_agent path to import the shared MCP client
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'genetic_agent', 'genetic_agent'))
    from genetic_agent.shared.mcp.zen_client import ZenClient as BaseZenClient
except ImportError:
    # Mock implementation for development
    class BaseZenClient:
        def __init__(self, base_url: str, config):
            self.base_url = base_url
            self.config = config

        async def plan_complex_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
            """Mock implementation of complex task planning."""
            return {
                "plan": f"Mock plan for: {task_data.get('description', 'Unknown task')}",
                "subtasks": [
                    {"id": "subtask_1", "description": "First subtask", "duration": 15},
                    {"id": "subtask_2", "description": "Second subtask", "duration": 15}
                ],
                "estimated_total": task_data.get('estimated_minutes', 30)
            }

class TaskOrchestratorZenClient(BaseZenClient):
    """Zen MCP client specialized for task orchestration and planning."""

    def __init__(self, base_url: str, config):
        """Initialize with task orchestration settings."""
        super().__init__(base_url, config)

    async def plan_task_breakdown(self, complex_task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen planner to break down complex tasks into manageable subtasks."""
        task_description = complex_task.get('description', 'Unknown task')
        complexity = complex_task.get('complexity', 0.5)
        estimated_duration = complex_task.get('estimated_minutes', 30)

        planning_prompt = f"""Break down this complex task into manageable subtasks for ADHD-friendly execution:

Task: {task_description}
Complexity: {complexity}
Total Duration: {estimated_duration} minutes

Context:
- Current energy: {context.get('energy_level', 'unknown')}
- Attention state: {context.get('attention_state', 'unknown')}
- Cognitive load: {context.get('cognitive_load', 0.5)}
- Available time: {context.get('available_time', 60)} minutes

Create a detailed breakdown that:
1. Divides the task into 3-7 logical subtasks
2. Estimates duration for each subtask (10-25 minutes each)
3. Identifies dependencies and optimal execution order
4. Includes ADHD-friendly accommodations
5. Provides progress checkpoints

Format: {{
  "subtasks": [
    {{
      "name": "subtask name",
      "description": "detailed description",
      "duration_minutes": 15,
      "dependencies": ["prerequisite task"],
      "adhd_accommodations": ["specific accommodations"]
    }}
  ],
  "execution_order": ["task1", "task2", "task3"],
  "total_duration": 45,
  "break_points": ["after task2", "after task4"],
  "progress_checkpoints": ["complete task1", "complete task3"],
  "risk_mitigation": ["strategies for common issues"],
  "confidence": 0.8
}}"""

        try:
            async with self:
                response = await self.planner(
                    step=planning_prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    model="gemini-2.5-pro"
                )

                return response.get('plan', {
                    'subtasks': [{
                        'name': 'Basic execution',
                        'description': task_description,
                        'duration_minutes': estimated_duration,
                        'dependencies': [],
                        'adhd_accommodations': ['Standard breaks']
                    }],
                    'execution_order': ['Basic execution'],
                    'total_duration': estimated_duration,
                    'break_points': [],
                    'progress_checkpoints': [],
                    'risk_mitigation': ['Standard practices'],
                    'confidence': 0.3
                })

        except Exception as e:
            print(f"Zen task breakdown planning failed: {e}")
            return {
                'subtasks': [{
                    'name': 'Fallback task',
                    'description': task_description,
                    'duration_minutes': min(estimated_duration, 25),
                    'dependencies': [],
                    'adhd_accommodations': ['Take breaks as needed']
                }],
                'execution_order': ['Fallback task'],
                'total_duration': estimated_duration,
                'break_points': [],
                'progress_checkpoints': [],
                'risk_mitigation': ['Fallback to basic execution'],
                'confidence': 0.2
            }

    async def prioritize_task_queue(self, task_queue: List[Dict[str, Any]], adhd_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen planner to intelligently prioritize tasks based on ADHD state and energy patterns."""
        task_summaries = [f"{i+1}. {t['description']} (complexity: {t.get('complexity', 0.5)}, duration: {t.get('estimated_minutes', 30)}min)"
                         for i, t in enumerate(task_queue)]

        prioritization_prompt = f"""Prioritize this task queue for optimal ADHD-friendly execution:

Tasks:
{chr(10).join(task_summaries)}

ADHD Context:
- Current energy: {adhd_context.get('energy_level', 'unknown')}
- Attention state: {adhd_context.get('attention_state', 'unknown')}
- Cognitive load: {adhd_context.get('cognitive_load', 0.5)}
- Time available: {adhd_context.get('available_time', 120)} minutes
- Peak energy hours: {adhd_context.get('peak_hours', 'unknown')}

Prioritize tasks considering:
1. Energy alignment (high-energy tasks first)
2. Attention compatibility (focus vs creative tasks)
3. Cognitive load distribution (avoid overload)
4. Task interdependencies (prerequisites first)
5. ADHD-friendly chunking (25-minute sessions)
6. Break scheduling (prevent hyperfocus)

Format: {{
  "prioritized_order": [task_indices],
  "execution_batches": [[task_indices_for_batch1], [task_indices_for_batch2]],
  "estimated_completion": "X hours Y minutes",
  "break_schedule": ["after batch 1", "after batch 2"],
  "energy_distribution": "high-medium-low or balanced",
  "rationale": "detailed reasoning for prioritization"
}}"""

        try:
            async with self:
                response = await self.planner(
                    step=prioritization_prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    model="gemini-2.5-pro"
                )

                plan = response.get('plan', '')
                # Parse the prioritization plan
                if 'prioritized_order' in plan:
                    return plan
                else:
                    # Fallback to simple prioritization
                    return {
                        'prioritized_order': list(range(len(task_queue))),
                        'execution_batches': [list(range(len(task_queue)))],
                        'estimated_completion': f"{sum(t.get('estimated_minutes', 30) for t in task_queue)} minutes",
                        'break_schedule': [],
                        'energy_distribution': 'sequential',
                        'rationale': 'Fallback to original order'
                    }

        except Exception as e:
            print(f"Zen task prioritization failed: {e}")
            return {
                'prioritized_order': list(range(len(task_queue))),
                'execution_batches': [list(range(len(task_queue)))],
                'estimated_completion': f"{sum(t.get('estimated_minutes', 30) for t in task_queue)} minutes",
                'break_schedule': [],
                'energy_distribution': 'sequential',
                'rationale': 'Zen prioritization unavailable'
            }