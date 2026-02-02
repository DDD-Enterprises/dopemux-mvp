"""PAL MCP client for ADHD Engine multi-model reasoning."""

from typing import Dict, Any, List, Optional
import sys
import os

# Add the genetic_agent path to import the shared MCP client
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'genetic_agent', 'genetic_agent'))

from genetic_agent.shared.mcp.pal_client import PALClient as BasePALClient

class ADHDPALClient(BasePALClient):
    """PAL MCP client specialized for ADHD Engine reasoning and planning."""

    def __init__(self, base_url: str, config):

import logging

logger = logging.getLogger(__name__)

        """Initialize with ADHD-specific settings."""
        super().__init__(base_url, config)

    async def assess_task_complexity(self, task_description: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen thinkdeep to assess task complexity for ADHD accommodations."""
        prompt = f"""Assess the cognitive complexity of this task for ADHD accommodation planning:

Task: {task_description}

User Context:
- Energy Level: {user_context.get('energy_level', 'unknown')}
- Attention State: {user_context.get('attention_state', 'unknown')}
- Current Cognitive Load: {user_context.get('cognitive_load', 'unknown')}

Analyze:
1. Task complexity (0.0-1.0 scale)
2. Required attention span (minutes)
3. Break points and timing
4. Cognitive load impact
5. Recommended accommodations

Format: {{
  "complexity_score": 0.7,
  "attention_span_required": 45,
  "recommended_breaks": ["after 25 minutes", "after 45 minutes"],
  "cognitive_impact": "high",
  "accommodations": ["25-minute focus sessions", "progress tracking"]
}}"""

        try:
            async with self:
                response = await self.thinkdeep(
                    step=prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    findings="Task complexity assessment for ADHD accommodations",
                    model="gemini-2.5-pro"
                )
                return response.get('reasoning', {
                    'complexity_score': 0.5,
                    'attention_span_required': 30,
                    'recommended_breaks': ['after 25 minutes'],
                    'cognitive_impact': 'medium',
                    'accommodations': ['standard accommodations']
                })
        except Exception as e:
            logger.error(f"Zen task complexity assessment failed: {e}")
            return {
                'complexity_score': 0.5,
                'attention_span_required': 30,
                'recommended_breaks': ['after 25 minutes'],
                'cognitive_impact': 'medium',
                'accommodations': ['standard accommodations']
            }

    async def recommend_break_strategy(self, current_state: Dict[str, Any], work_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen planner to recommend optimal break timing and duration."""
        prompt = f"""Plan optimal break strategy for ADHD accommodation:

Current State:
- Energy Level: {current_state.get('energy_level', 'unknown')}
- Attention State: {current_state.get('attention_state', 'unknown')}
- Time Working: {current_state.get('minutes_since_last_break', 0)} minutes
- Cognitive Load: {current_state.get('cognitive_load', 'unknown')}

Work Context:
- Task Type: {work_context.get('task_type', 'unknown')}
- Complexity: {work_context.get('complexity', 0.5)}
- Progress Made: {work_context.get('progress_percentage', 0)}%

Determine optimal break strategy considering ADHD patterns and current state.

Format: {{
  "break_recommended": true,
  "break_duration_minutes": 5,
  "break_type": "short",
  "timing": "immediate",
  "reasoning": "detailed explanation",
  "post_break_energy_boost": 0.2
}}"""

        try:
            async with self:
                response = await self.planner(
                    step=prompt,
                    step_number=1,
                    total_steps=1,
                    next_step_required=False,
                    model="gemini-2.5-pro"
                )

                plan = response.get('plan', '')
                # Parse the plan to extract structured break recommendation
                if 'break_recommended' in plan.lower() or 'immediate' in plan.lower():
                    return {
                        'break_recommended': True,
                        'break_duration_minutes': 5,
                        'break_type': 'short',
                        'timing': 'immediate',
                        'reasoning': plan,
                        'post_break_energy_boost': 0.15
                    }
                else:
                    return {
                        'break_recommended': False,
                        'break_duration_minutes': 0,
                        'break_type': 'none',
                        'timing': 'later',
                        'reasoning': plan,
                        'post_break_energy_boost': 0.0
                    }
        except Exception as e:
            logger.error(f"Zen break strategy planning failed: {e}")
            return {
                'break_recommended': False,
                'break_duration_minutes': 0,
                'break_type': 'none',
                'timing': 'later',
                'reasoning': 'Planning unavailable',
                'post_break_energy_boost': 0.0
            }