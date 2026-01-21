"""
ADHD Engine Integration for Working Memory Assistant

This module handles integration with the ADHD Engine microservice to provide
real-time energy level, attention state, and cognitive load awareness for
ADHD-optimized snapshots and recovery.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import aiohttp
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ADHDEngineClient:
    """Client for interacting with ADHD Engine microservice"""

    def __init__(self, base_url: str = "http://localhost:8095"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_energy_level(self, user_id: str) -> Dict[str, Any]:
        """Get current energy level from ADHD Engine"""
        url = f"{self.base_url}/api/v1/energy-level"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                # Return default energy level on failure
                return {
                    "energy_level": 0.5,
                    "energy_state": "unknown",
                    "confidence": 0.0
                }

    async def get_attention_state(self, user_id: str) -> Dict[str, Any]:
        """Get current attention state"""
        url = f"{self.base_url}/api/v1/attention-state"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {
                    "attention_state": "unknown",
                    "confidence": 0.0
                }

    async def get_cognitive_load(self, user_id: str) -> Dict[str, Any]:
        """Get current cognitive load"""
        url = f"{self.base_url}/api/v1/cognitive-load"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {
                    "cognitive_load": 0.5,
                    "load_state": "unknown",
                    "confidence": 0.0
                }

@dataclass
class ADHDContext:
    """ADHD context data for WMA snapshots"""
    energy_level: float
    attention_state: str
    cognitive_load: float
    context_switch_detected: bool
    break_recommended: bool
    session_duration: int
    hyperfocus_protection: bool

class ADHDEngineIntegration:
    """Integration layer between WMA and ADHD Engine"""

    def __init__(self, base_url: str = "http://localhost:8095"):
        self.client = ADHDEngineClient(base_url)

    async def get_adhd_context(self, user_id: str) -> ADHDContext:
        """Get comprehensive ADHD context"""
        # Parallel async calls for performance
        energy_task = self.client.get_energy_level(user_id)
        attention_task = self.client.get_attention_state(user_id)
        load_task = self.client.get_cognitive_load(user_id)

        energy, attention, load = await asyncio.gather(energy_task, attention_task, load_task)

        return ADHDContext(
            energy_level=energy.get("energy_level", 0.5),
            attention_state=attention.get("attention_state", "unknown"),
            cognitive_load=load.get("cognitive_load", 0.5),
            context_switch_detected=attention.get("context_switch_detected", False),
            break_recommended=load.get("break_recommended", False),
            session_duration=energy.get("session_duration", 0),
            hyperfocus_protection=energy.get("hyperfocus_protection", False)
        )

async def test_adhd_integration():
    """Test ADHD Engine integration"""
    async with ADHDEngineClient() as client:
        context = await get_adhd_context("test_user")
        logger.info(f"ADHD Context: {context}")

if __name__ == "__main__":
    asyncio.run(test_adhd_integration())
