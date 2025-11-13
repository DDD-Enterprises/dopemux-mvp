"""
Monitoring Dashboard DopeconBridge Adapter

Monitoring and metrics tracking via DopeconBridge for:
- Service health monitoring
- Performance metrics
- Alert management
- Dashboard state
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


class MonitoringDashboardBridgeAdapter:
    """DopeconBridge adapter for Monitoring Dashboard service"""
    
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
        logger.info(f"✅ Monitoring Dashboard DopeconBridge adapter initialized (workspace: {workspace_id})")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def log_service_health(
        self,
        service_name: str,
        health_status: str,
        metrics: Dict[str, Any],
    ) -> bool:
        """Log service health status"""
        try:
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="service_health",
                key=f"{service_name}_{datetime.utcnow().isoformat()}",
                value={
                    "service": service_name,
                    "status": health_status,
                    "metrics": metrics,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            
            # Publish health event
            await self.client.publish_event(
                event_type="monitoring.health.updated",
                data={
                    "service": service_name,
                    "status": health_status,
                    "workspace_id": self.workspace_id,
                },
                source="monitoring-dashboard",
            )
            
            logger.info(f"Logged health for {service_name}: {health_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to log service health: {e}")
            return False
    
    async def log_performance_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_type: str = "gauge",
        tags: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Log performance metric"""
        try:
            await self.client.publish_event(
                event_type="monitoring.metric.recorded",
                data={
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metric_type": metric_type,
                    "tags": tags or {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "workspace_id": self.workspace_id,
                },
                source="monitoring-dashboard",
            )
            
            logger.debug(f"Logged metric {metric_name}: {metric_value}")
            return True
        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}")
            return False
    
    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create monitoring alert"""
        try:
            alert_id = f"alert_{datetime.utcnow().isoformat()}"
            
            await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="monitoring_alerts",
                key=alert_id,
                value={
                    "alert_id": alert_id,
                    "type": alert_type,
                    "severity": severity,
                    "message": message,
                    "metadata": metadata or {},
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "active",
                },
            )
            
            # Publish alert event
            await self.client.publish_event(
                event_type="monitoring.alert.created",
                data={
                    "alert_id": alert_id,
                    "type": alert_type,
                    "severity": severity,
                    "message": message,
                    "workspace_id": self.workspace_id,
                },
                source="monitoring-dashboard",
            )
            
            logger.warning(f"Created alert [{severity}] {alert_type}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return False
    
    async def get_active_alerts(
        self,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="monitoring_alerts",
                limit=limit,
            )
            
            alerts = [r.get("value", {}) for r in results]
            
            # Filter by severity if specified
            if severity:
                alerts = [a for a in alerts if a.get("severity") == severity]
            
            # Filter only active
            alerts = [a for a in alerts if a.get("status") == "active"]
            
            return alerts
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Resolve an alert"""
        try:
            await self.client.publish_event(
                event_type="monitoring.alert.resolved",
                data={
                    "alert_id": alert_id,
                    "resolved_at": datetime.utcnow().isoformat(),
                    "notes": resolution_notes,
                    "workspace_id": self.workspace_id,
                },
                source="monitoring-dashboard",
            )
            
            logger.info(f"Resolved alert: {alert_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    async def save_dashboard_state(
        self,
        dashboard_id: str,
        dashboard_config: Dict[str, Any],
    ) -> bool:
        """Save dashboard configuration state"""
        try:
            success = await self.client.save_custom_data(
                workspace_id=self.workspace_id,
                category="dashboard_states",
                key=dashboard_id,
                value={
                    "dashboard_id": dashboard_id,
                    "config": dashboard_config,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )
            
            logger.info(f"Saved dashboard state: {dashboard_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to save dashboard state: {e}")
            return False
    
    async def get_dashboard_state(
        self,
        dashboard_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get dashboard configuration state"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="dashboard_states",
                key=dashboard_id,
                limit=1,
            )
            
            if results:
                return results[0].get("value", {}).get("config", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get dashboard state: {e}")
            return None
    
    async def get_service_metrics(
        self,
        service_name: str,
        metric_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get historical metrics for a service"""
        try:
            results = await self.client.get_custom_data(
                workspace_id=self.workspace_id,
                category="service_health",
                limit=limit,
            )
            
            # Filter for this service
            service_metrics = [
                r.get("value", {})
                for r in results
                if r.get("value", {}).get("service") == service_name
            ]
            
            return service_metrics
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return []
