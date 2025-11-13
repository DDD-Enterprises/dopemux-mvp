"""DopeconBridge integration for Genetic Agent.

Provides event publishing and decision tracking for genetic algorithm iterations.
"""

import logging
from typing import Any, Dict, List, Optional

from services.shared.dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class GeneticAgentBridgeAdapter:
    """Adapter for Genetic Agent to use DopeconBridge.
    
    Handles:
    - Publishing genetic iteration events
    - Tracking repair decisions and outcomes
    - Storing population fitness data
    - Recording mutation/crossover events
    """

    def __init__(
        self,
        *,
        workspace_id: str,
        base_url: str,
        token: Optional[str] = None,
        source_plane: str = "cognitive_plane",
    ):
        """Initialize the adapter.
        
        Args:
            workspace_id: Current workspace ID
            base_url: DopeconBridge base URL
            token: Optional auth token
            source_plane: Source plane identifier
        """
        self.workspace_id = workspace_id
        config = DopeconBridgeConfig(
            base_url=base_url,
            token=token,
            source_plane=source_plane,
        )
        self._client = AsyncDopeconBridgeClient(config=config)
        logger.info(
            f"✅ GeneticAgentBridgeAdapter initialized for workspace {workspace_id}"
        )

    async def publish_iteration_start(
        self,
        generation: int,
        population_size: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Publish genetic iteration start event."""
        try:
            await self._client.publish_event(
                event_type="genetic.iteration.start",
                data={
                    "workspace_id": self.workspace_id,
                    "generation": generation,
                    "population_size": population_size,
                    "metadata": metadata or {},
                },
                source="genetic_agent",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish iteration start: {e}")
            return False

    async def publish_iteration_complete(
        self,
        generation: int,
        best_fitness: float,
        avg_fitness: float,
        solutions: List[Dict[str, Any]],
    ) -> bool:
        """Publish genetic iteration completion event."""
        try:
            await self._client.publish_event(
                event_type="genetic.iteration.complete",
                data={
                    "workspace_id": self.workspace_id,
                    "generation": generation,
                    "best_fitness": best_fitness,
                    "avg_fitness": avg_fitness,
                    "solution_count": len(solutions),
                    "top_solutions": solutions[:3],  # Top 3 only
                },
                source="genetic_agent",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish iteration complete: {e}")
            return False

    async def publish_repair_decision(
        self,
        task_id: str,
        strategy: str,
        success: bool,
        fitness_score: float,
        mutations_applied: int,
    ) -> bool:
        """Publish a repair decision outcome."""
        try:
            await self._client.publish_event(
                event_type="genetic.repair.decision",
                data={
                    "workspace_id": self.workspace_id,
                    "task_id": task_id,
                    "strategy": strategy,
                    "success": success,
                    "fitness_score": fitness_score,
                    "mutations_applied": mutations_applied,
                },
                source="genetic_agent",
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish repair decision: {e}")
            return False

    async def store_population_data(
        self,
        generation: int,
        population: List[Dict[str, Any]],
    ) -> bool:
        """Store population data in KG custom_data."""
        try:
            await self._client.save_custom_data(
                workspace_id=self.workspace_id,
                category="genetic_populations",
                key=f"gen_{generation}",
                value={
                    "generation": generation,
                    "population": population,
                    "size": len(population),
                },
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store population data: {e}")
            return False

    async def get_historical_populations(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical population data."""
        try:
            data = await self._client.get_custom_data(
                workspace_id=self.workspace_id,
                category="genetic_populations",
                limit=limit,
            )
            return data
        except Exception as e:
            logger.error(f"Failed to get historical populations: {e}")
            return []

    async def search_similar_repairs(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for similar past repair decisions."""
        try:
            result = await self._client.related_text(
                query=query,
                workspace_id=self.workspace_id,
                k=k,
            )
            return result.get("data", []) if result else []
        except Exception as e:
            logger.error(f"Failed to search similar repairs: {e}")
            return []

    async def close(self):
        """Close the bridge client."""
        await self._client.close()
