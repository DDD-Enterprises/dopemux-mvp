#!/usr/bin/env python3
"""
Working Memory Assistant - ADHD Engine Client
Integrates with ADHD Engine for real-time energy monitoring and cognitive load assessment.
"""

import os

import logging

logger = logging.getLogger(__name__)

import asyncio
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class ADHDEngineClient:
    """
    Client for ADHD Engine integration with Working Memory Assistant.
    Provides real-time ADHD state monitoring and context correlation.
    """

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv('ADHD_ENGINE_URL', 'http://localhost:8095')
        self.api_key = api_key or os.getenv('ADHD_ENGINE_API_KEY', 'dev-key-123')
        self.client = httpx.AsyncClient(
            timeout=5.0,
            headers={'Authorization': f'Bearer {self.api_key}'}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_energy_level(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current energy level for user"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/energy-level/{user_id}")
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"ADHD Engine energy level query failed: {e}")
            return None

    async def get_attention_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current attention state for user"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/attention-state/{user_id}")
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"ADHD Engine attention state query failed: {e}")
            return None

    async def get_cognitive_load(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current cognitive load for user"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/cognitive-load/{user_id}")
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"ADHD Engine cognitive load query failed: {e}")
            return None

    async def get_break_recommendation(self, user_id: str, work_duration_minutes: int = 25) -> Optional[Dict[str, Any]]:
        """Get break recommendation for user"""
        try:
            response = await self.client.post(f"{self.base_url}/api/v1/recommend-break", json={
                "user_id": user_id,
                "work_duration": work_duration_minutes
            })
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            logger.error(f"ADHD Engine break recommendation query failed: {e}")
            return None

    async def assess_task_complexity(self, task_description: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Assess task complexity for ADHD optimization"""
        try:
            payload = {
                'task_description': task_description,
                'user_id': user_id
            }
            response = await self.client.post(f"{self.base_url}/api/v1/assess-task", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ADHD Engine task assessment failed: {e}")
            return None

    async def get_adhd_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive ADHD context for user"""
        # Query all ADHD metrics in parallel
        tasks = [
            self.get_energy_level(user_id),
            self.get_attention_state(user_id),
            self.get_cognitive_load(user_id),
            self.get_break_recommendation(user_id)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        adhd_context = {
            'timestamp': datetime.now().isoformat(),
            'energy_level': None,
            'attention_state': None,
            'cognitive_load': None,
            'break_recommendation': None,
            'is_available': False
        }

        # Process results
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                if i == 0:
                    adhd_context['energy_level'] = result
                elif i == 1:
                    adhd_context['attention_state'] = result
                elif i == 2:
                    adhd_context['cognitive_load'] = result
                elif i == 3:
                    adhd_context['break_recommendation'] = result

        # Determine if ADHD Engine is available
        adhd_context['is_available'] = any([
            adhd_context['energy_level'],
            adhd_context['attention_state'],
            adhd_context['cognitive_load']
        ])

        return adhd_context

    async def send_context_correlation(self, user_id: str, wma_snapshot_id: str, context_data: Dict[str, Any]) -> bool:
        """Send WMA context data to ADHD Engine for correlation and learning"""
        try:
            payload = {
                'user_id': user_id,
                'wma_snapshot_id': wma_snapshot_id,
                'context_data': context_data,
                'timestamp': datetime.now().isoformat()
            }

            # ADHD Engine might have an endpoint for this, or we could use existing ones
            # For now, we'll use a placeholder - this would need ADHD Engine enhancement
            logger.info(f"Would send context correlation to ADHD Engine: {user_id}:{wma_snapshot_id}")
            return True

        except Exception as e:
            logger.error(f"ADHD Engine context correlation failed: {e}")
            return False

    async def adapt_recovery_to_adhd_state(self, user_id: str, base_recovery_stage: str) -> str:
        """
        Adapt recovery stage based on current ADHD state.
        Returns optimal recovery stage (essential/detailed/complete).
        """
        adhd_context = await self.get_adhd_context(user_id)

        if not adhd_context['is_available']:
            return base_recovery_stage  # Fall back to requested stage

        # Adapt based on ADHD state
        energy_level = adhd_context.get('energy_level', {}).get('level', 0.5)
        attention_state = adhd_context.get('attention_state', {}).get('state', 'scattered')
        cognitive_load = adhd_context.get('cognitive_load', {}).get('load', 0.5)

        # Low energy: Start with essential only
        if energy_level < 0.3:
            return 'essential'

        # High cognitive load: Be gentle with information
        if cognitive_load > 0.8:
            return 'essential' if base_recovery_stage == 'complete' else base_recovery_stage

        # Focused attention: Can handle more information
        if attention_state == 'focused' and energy_level > 0.6:
            return 'detailed' if base_recovery_stage == 'essential' else base_recovery_stage

        # Scattered attention: Keep it simple
        if attention_state == 'scattered':
            return 'essential'

        return base_recovery_stage

    async def should_snapshot_based_on_adhd_state(self, user_id: str) -> bool:
        """
        Determine if snapshot should be created based on ADHD state.
        Returns True if significant change detected or manual request.
        """
        adhd_context = await self.get_adhd_context(user_id)

        if not adhd_context['is_available']:
            return True  # Default to allowing snapshots

        # Check for significant state changes
        energy_level = adhd_context.get('energy_level', {}).get('level', 0.5)
        attention_state = adhd_context.get('attention_state', {}).get('state', 'neutral')

        # Significant energy changes
        if energy_level < 0.2 or energy_level > 0.9:
            return True

        # Attention state changes
        if attention_state in ['transitioning', 'scattered']:
            return True

        # Break recommendations
        break_rec = adhd_context.get('break_recommendation', {})
        if break_rec.get('recommended', False):
            return True

        return False  # No significant changes detected

# Global client instance
_adhd_client = None

def get_adhd_engine_client() -> ADHDEngineClient:
    """Get global ADHD Engine client instance"""
    global _adhd_client
    if _adhd_client is None:
        _adhd_client = ADHDEngineClient()
    return _adhd_client

async def close_adhd_engine_client():
    """Close global ADHD Engine client"""
    global _adhd_client
    if _adhd_client:
        await _adhd_client.client.aclose()
        _adhd_client = None