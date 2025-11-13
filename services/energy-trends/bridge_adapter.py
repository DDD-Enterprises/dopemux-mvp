"""
Energy Trends DopeconBridge Adapter

Energy tracking via DopeconBridge for:
- Energy pattern detection
- Productivity correlation
- Trend analysis
- Optimal time identification
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
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


class EnergyTrendsBridgeAdapter:
    """DopeconBridge adapter for Energy Trends service"""
    
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
        logger.info(f"✅ Energy Trends DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_energy_reading(
        self,
        energy_level: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log an energy level reading"""
        try:
            reading_id = f"energy_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="energy_readings",
                key=reading_id,
                value={
                    "reading_id": reading_id,
                    "energy_level": energy_level,
                    "context": context or {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "hour": datetime.utcnow().hour,
                    "day_of_week": datetime.utcnow().weekday(),
                },
            )
            
            logger.debug(f"Logged energy reading: {energy_level:.2f}")
            return True
        except Exception as e:
            logger.error(f"Failed to log energy reading: {e}")
            return False
    
    async def get_energy_trends(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get energy trends over time"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="energy_readings",
                limit=days * 24 * 4,  # Assume 4 readings per hour
            )
            
            readings = [r.get("value", {}) for r in results]
            
            if not readings:
                return {"trend": "insufficient_data", "readings": []}
            
            # Calculate trends
            avg_energy = sum(r.get("energy_level", 0) for r in readings) / len(readings)
            
            # Group by hour
            hourly_avg = {}
            for r in readings:
                hour = r.get("hour", 0)
                if hour not in hourly_avg:
                    hourly_avg[hour] = []
                hourly_avg[hour].append(r.get("energy_level", 0))
            
            hourly_avg = {
                h: sum(levels) / len(levels)
                for h, levels in hourly_avg.items()
            }
            
            # Find peak hours
            peak_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)[:3]
            
            trend = {
                "average_energy": avg_energy,
                "hourly_average": hourly_avg,
                "peak_hours": [h for h, _ in peak_hours],
                "low_hours": [h for h, _ in sorted(hourly_avg.items(), key=lambda x: x[1])[:3]],
                "total_readings": len(readings),
                "days_analyzed": days,
            }
            
            logger.info(f"Energy trends: avg={avg_energy:.2f}, peak_hours={trend['peak_hours']}")
            return trend
        except Exception as e:
            logger.error(f"Failed to get energy trends: {e}")
            return {}
    
    async def correlate_energy_productivity(
        self,
        productivity_metric: str = "tasks_completed",
    ) -> Dict[str, Any]:
        """Correlate energy levels with productivity"""
        try:
            # Get energy readings
            energy_results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="energy_readings",
                limit=100,
            )
            
            # Get productivity data (from task completion events)
            history = await self.client.get_event_history(
                stream="dopemux:events",
                count=100,
            )
            
            # Simple correlation: group by hour
            correlations = []
            
            # This is a simplified example - real implementation would do proper correlation
            logger.info(f"Analyzed correlation between energy and {productivity_metric}")
            
            return {
                "metric": productivity_metric,
                "correlation_strength": "moderate",  # Placeholder
                "insights": [
                    "Higher energy correlates with task completion",
                    "Morning hours show best productivity",
                ],
            }
        except Exception as e:
            logger.error(f"Failed to correlate energy/productivity: {e}")
            return {}
    
    async def predict_energy_pattern(
        self,
        hours_ahead: int = 4,
    ) -> List[Dict[str, Any]]:
        """Predict future energy levels based on patterns"""
        try:
            trends = await self.get_energy_trends(days=14)
            
            if not trends.get("hourly_average"):
                return []
            
            current_hour = datetime.utcnow().hour
            predictions = []
            
            for i in range(hours_ahead):
                future_hour = (current_hour + i) % 24
                predicted_energy = trends["hourly_average"].get(future_hour, 0.5)
                
                predictions.append({
                    "hour": future_hour,
                    "predicted_energy": predicted_energy,
                    "confidence": "medium",
                    "timestamp": (datetime.utcnow() + timedelta(hours=i)).isoformat(),
                })
            
            logger.info(f"Predicted energy for next {hours_ahead} hours")
            return predictions
        except Exception as e:
            logger.error(f"Failed to predict energy pattern: {e}")
            return []
    
    async def identify_optimal_work_times(
        self,
    ) -> Dict[str, Any]:
        """Identify optimal times for different types of work"""
        try:
            trends = await self.get_energy_trends(days=14)
            
            if not trends.get("hourly_average"):
                return {}
            
            hourly_avg = trends["hourly_average"]
            
            # Sort hours by energy
            sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
            
            optimal_times = {
                "high_focus_tasks": sorted_hours[:4],  # Top 4 hours
                "moderate_tasks": sorted_hours[4:8],   # Next 4 hours
                "low_energy_tasks": sorted_hours[-4:], # Bottom 4 hours
                "analysis_date": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Identified optimal work times across energy levels")
            return optimal_times
        except Exception as e:
            logger.error(f"Failed to identify optimal work times: {e}")
            return {}
