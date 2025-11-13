"""
Break Suggester DopeconBridge Adapter

Break management via DopeconBridge for:
- Break time recommendations
- Energy level monitoring
- Break effectiveness tracking
- Recovery optimization
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import sys
import logging

# Add shared modules
SHARED_DIR = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class BreakSuggesterBridgeAdapter:
    """DopeconBridge adapter for Break Suggester service"""
    
    def __init__(
        self,
        workspace_id: str,
        base_url: str = None,
        token: str = None,
    ):
        self.workspace_id = workspace_id
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
                timeout=config.timeout,
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(f"✅ Break Suggester DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def suggest_break(
        self,
        energy_level: float,
        work_duration_minutes: int,
        last_break_minutes_ago: int,
    ) -> Dict[str, Any]:
        """Suggest a break based on current state"""
        try:
            suggestion_id = f"break_suggest_{datetime.utcnow().isoformat()}"
            
            # Calculate suggestion
            should_break = (
                energy_level < 0.3 or
                work_duration_minutes > 90 or
                last_break_minutes_ago > 120
            )
            
            urgency = "high" if energy_level < 0.2 else "medium" if should_break else "low"
            
            suggestion = {
                "suggestion_id": suggestion_id,
                "should_break": should_break,
                "urgency": urgency,
                "recommended_duration": 5 if energy_level < 0.2 else 15,
                "reason": self._get_break_reason(energy_level, work_duration_minutes, last_break_minutes_ago),
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Save suggestion
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="break_suggestions",
                key=suggestion_id,
                value=suggestion,
            )
            
            # Publish event if break recommended
            if should_break:
                await self.client.publish_event(
                    event_type="break.suggested",
                    data={
                        "urgency": urgency,
                        "duration": suggestion["recommended_duration"],
                        "workspace_id": self.workspace_id,
                    },
                    source="break-suggester",
                )
            
            logger.info(f"Break suggestion: {urgency} urgency, should_break={should_break}")
            return suggestion
        except Exception as e:
            logger.error(f"Failed to suggest break: {e}")
            return {"should_break": False, "error": str(e)}
    
    def _get_break_reason(self, energy_level: float, work_duration: int, last_break: int) -> str:
        """Determine the primary reason for break suggestion"""
        if energy_level < 0.2:
            return "Energy critically low - immediate break needed"
        elif energy_level < 0.3:
            return "Energy declining - break recommended"
        elif work_duration > 90:
            return "Work session exceeded 90 minutes"
        elif last_break > 120:
            return "Over 2 hours since last break"
        else:
            return "Maintaining optimal energy levels"
    
    async def log_break_taken(
        self,
        duration_minutes: int,
        break_type: str = "standard",
        activities: Optional[List[str]] = None,
    ) -> bool:
        """Log a break that was taken"""
        try:
            break_id = f"break_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="breaks_taken",
                key=break_id,
                value={
                    "break_id": break_id,
                    "duration": duration_minutes,
                    "type": break_type,
                    "activities": activities or [],
                    "started_at": datetime.utcnow().isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="break.taken",
                data={
                    "duration": duration_minutes,
                    "type": break_type,
                    "workspace_id": self.workspace_id,
                },
                source="break-suggester",
            )
            
            logger.info(f"Logged break: {duration_minutes}min ({break_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to log break: {e}")
            return False
    
    async def log_energy_level(
        self,
        energy_level: float,
        factors: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log current energy level"""
        try:
            await self.client.publish_event(
                event_type="break.energy.updated",
                data={
                    "energy_level": energy_level,
                    "factors": factors or {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="break-suggester",
            )
            
            logger.debug(f"Logged energy level: {energy_level:.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to log energy level: {e}")
            return False
    
    async def get_break_history(
        self,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent break history"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="breaks_taken",
                limit=limit,
            )
            
            breaks = [r.get("value", {}) for r in results]
            return breaks
        except Exception as e:
            logger.error(f"Failed to get break history: {e}")
            return []
    
    async def analyze_break_effectiveness(
        self,
        break_id: str,
        post_break_energy: float,
        pre_break_energy: float,
    ) -> bool:
        """Analyze how effective a break was"""
        try:
            effectiveness = post_break_energy - pre_break_energy
            
            await self.client.publish_event(
                event_type="break.effectiveness.analyzed",
                data={
                    "break_id": break_id,
                    "effectiveness": effectiveness,
                    "pre_energy": pre_break_energy,
                    "post_energy": post_break_energy,
                    "workspace_id": self.workspace_id,
                },
                source="break-suggester",
            )
            
            logger.info(f"Break effectiveness: {effectiveness:+.2f} energy change")
            return True
        except Exception as e:
            logger.error(f"Failed to analyze break effectiveness: {e}")
            return False
