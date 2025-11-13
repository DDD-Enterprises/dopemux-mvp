"""
Dope Brainz DopeconBridge Adapter

Unified adapter for all intelligence/ML services to interact via DopeconBridge.

Covers:
- ML predictions
- Risk assessments
- Session intelligence
- Working memory
- Pattern learning
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import sys
import logging

# Add shared modules
SHARED_DIR = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(SHARED_DIR))

from dopecon_bridge_client import (
    AsyncDopeconBridgeClient,
    DopeconBridgeConfig,
)

logger = logging.getLogger(__name__)


class DopeBrainzBridgeAdapter:
    """
    Unified bridge adapter for Dope Brainz intelligence services.
    
    Handles:
    - ML predictions
    - Risk assessments
    - Session intelligence
    - Working memory
    - Pattern learning
    """
    
    def __init__(
        self,
        workspace_id: str,
        service_name: str = "dope-brainz",
        base_url: str = None,
        token: str = None,
    ):
        self.workspace_id = workspace_id
        self.service_name = service_name
        
        config = DopeconBridgeConfig.from_env()
        if base_url:
            config = DopeconBridgeConfig(
                base_url=base_url,
                token=token or config.token,
                source_plane="cognitive_plane",
                timeout=config.timeout,
            )
        
        self.client = AsyncDopeconBridgeClient(config=config)
        logger.info(f"✅ Dope Brainz DopeconBridge adapter initialized (service: {service_name}, workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_prediction(
        self,
        prediction_type: str,
        prediction_data: Dict[str, Any],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log ML prediction via DopeconBridge"""
        try:
            # Save prediction
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="ml_predictions",
                key=f"{prediction_type}_{datetime.utcnow().isoformat()}",
                value={
                    "type": prediction_type,
                    "data": prediction_data,
                    "confidence": confidence,
                    "metadata": metadata or {},
                    "service": self.service_name,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            
            # Publish event
            if success:
                await self.client.publish_event(
                    event_type="brainz.prediction.logged",
                    data={
                        "prediction_type": prediction_type,
                        "confidence": confidence,
                        "workspace_id": self.workspace_id,
                    },
                    source=self.service_name,
                )
            
            logger.info(f"Logged prediction: {prediction_type} (confidence: {confidence})")
            return success
        except Exception as e:
            logger.error(f"Failed to log prediction: {e}")
            return False
    
    async def log_risk_assessment(
        self,
        task_id: str,
        risk_score: float,
        risk_factors: List[str],
        recommendations: Optional[List[str]] = None,
    ) -> bool:
        """Log risk assessment"""
        try:
            # Save risk assessment
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="risk_assessments",
                key=f"task_{task_id}_{datetime.utcnow().isoformat()}",
                value={
                    "task_id": task_id,
                    "risk_score": risk_score,
                    "risk_factors": risk_factors,
                    "recommendations": recommendations or [],
                    "assessed_at": datetime.utcnow().isoformat(),
                },
            )
            
            # Publish event
            await self.client.publish_event(
                event_type="brainz.risk_assessed",
                data={
                    "task_id": task_id,
                    "risk_score": risk_score,
                    "risk_factors": risk_factors,
                    "workspace_id": self.workspace_id,
                },
                source=self.service_name,
            )
            
            logger.info(f"Logged risk assessment for task {task_id}: score={risk_score}")
            return True
        except Exception as e:
            logger.error(f"Failed to log risk assessment: {e}")
            return False
    
    async def save_learned_pattern(
        self,
        pattern_type: str,
        pattern_data: Dict[str, Any],
        confidence: float = 1.0,
    ) -> bool:
        """Save learned pattern"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="learned_patterns",
                key=f"{pattern_type}_{datetime.utcnow().isoformat()}",
                value={
                    "type": pattern_type,
                    "pattern": pattern_data,
                    "confidence": confidence,
                    "learned_at": datetime.utcnow().isoformat(),
                    "service": self.service_name,
                },
            )
            
            if success:
                await self.client.publish_event(
                    event_type="brainz.pattern.learned",
                    data={
                        "pattern_type": pattern_type,
                        "confidence": confidence,
                        "workspace_id": self.workspace_id,
                    },
                    source=self.service_name,
                )
            
            logger.info(f"Saved learned pattern: {pattern_type}")
            return success
        except Exception as e:
            logger.error(f"Failed to save learned pattern: {e}")
            return False
    
    async def get_learned_patterns(
        self,
        pattern_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get learned patterns"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="learned_patterns",
                key=pattern_type,
                limit=limit,
            )
            return [r.get("value", {}) for r in results]
        except Exception as e:
            logger.error(f"Failed to get learned patterns: {e}")
            return []
    
    async def log_session_intelligence(
        self,
        session_id: str,
        intelligence_data: Dict[str, Any],
    ) -> bool:
        """Log session intelligence data"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="session_intelligence",
                key=session_id,
                value={
                    "session_id": session_id,
                    "data": intelligence_data,
                    "logged_at": datetime.utcnow().isoformat(),
                },
            )
            
            await self.client.publish_event(
                event_type="brainz.session.analyzed",
                data={
                    "session_id": session_id,
                    "workspace_id": self.workspace_id,
                },
                source=self.service_name,
            )
            
            logger.info(f"Logged session intelligence: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log session intelligence: {e}")
            return False
    
    async def save_working_memory_state(
        self,
        memory_id: str,
        memory_data: Dict[str, Any],
    ) -> bool:
        """Save working memory state"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="working_memory",
                key=memory_id,
                value={
                    "memory_id": memory_id,
                    "state": memory_data,
                    "saved_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Saved working memory state: {memory_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to save working memory state: {e}")
            return False
    
    async def get_working_memory_state(
        self,
        memory_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get working memory state"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="working_memory",
                key=memory_id,
                limit=1,
            )
            if results:
                return results[0].get("value", {}).get("state", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get working memory state: {e}")
            return None
    
    async def publish_intelligence_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> bool:
        """Publish a Dope Brainz intelligence event"""
        try:
            await self.client.publish_event(
                event_type=f"brainz.{event_type}",
                data={**data, "workspace_id": self.workspace_id},
                source=self.service_name,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish intelligence event: {e}")
            return False
