#!/usr/bin/env python3
"""
Platform Evolution Monitoring Dashboard
Real-time monitoring of Context7-first multi-agent Claude Code platform

Tracks:
- Token usage across agent clusters
- Context7 integration effectiveness  
- Agent performance and health
- Cross-agent collaboration metrics
- Platform-wide optimization opportunities
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import docker
import psutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class AgentMetrics:
    agent_name: str
    cluster: str
    status: AgentStatus
    token_usage: int
    token_limit: int
    context7_queries: int
    context7_success_rate: float
    operations_completed: int
    avg_response_time: float
    cpu_usage: float
    memory_usage: float
    last_heartbeat: datetime
    
    @property
    def token_utilization(self) -> float:
        return (self.token_usage / self.token_limit) * 100 if self.token_limit > 0 else 0
    
    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        factors = [
            (100 - self.token_utilization) * 0.3,  # Lower token usage is better
            self.context7_success_rate * 0.3,      # Context7 integration effectiveness
            (100 - self.cpu_usage) * 0.2,          # CPU efficiency
            (100 - self.memory_usage) * 0.2        # Memory efficiency
        ]
        return sum(factors)

@dataclass
class PlatformMetrics:
    total_agents: int
    healthy_agents: int
    total_token_usage: int
    total_token_budget: int = 93000
    context7_integration_rate: float
    operations_per_minute: int
    avg_context7_response_time: float
    cross_agent_collaborations: int
    blocked_operations: int
    platform_efficiency_score: float

class PlatformMonitor:
    def __init__(self):
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.platform_metrics: PlatformMetrics = PlatformMetrics(
            total_agents=0, healthy_agents=0, total_token_usage=0,
            context7_integration_rate=0.0, operations_per_minute=0,
            avg_context7_response_time=0.0, cross_agent_collaborations=0,
            blocked_operations=0, platform_efficiency_score=0.0
        )
        self.docker_client = docker.from_env()
        self.metrics_history: List[Dict[str, Any]] = []
        
    async def collect_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """Collect metrics from all running agents"""
        
        agent_configs = {
            "context7_agent": {"cluster": "research", "token_limit": 8000},
            "exa_agent": {"cluster": "research", "token_limit": 10000},
            "serena_agent": {"cluster": "implementation", "token_limit": 15000},
            "taskmaster_agent": {"cluster": "implementation", "token_limit": 12000},
            "zen_reviewer": {"cluster": "quality", "token_limit": 15000},
            "testing_agent": {"cluster": "quality", "token_limit": 8000},
            "conport_agent": {"cluster": "coordination", "token_limit": 8000},
            "openmemory_agent": {"cluster": "coordination", "token_limit": 5000}
        }
        
        collected_metrics = {}
        
        for agent_name, config in agent_configs.items():
            try:
                metrics = await self.get_agent_health(agent_name, config)
                collected_metrics[agent_name] = metrics
                logger.info(f"Collected metrics for {agent_name}")
            except Exception as e:
                logger.error(f"Failed to collect metrics for {agent_name}: {e}")
                # Create offline metric
                collected_metrics[agent_name] = AgentMetrics(
                    agent_name=agent_name,
                    cluster=config["cluster"],
                    status=AgentStatus.OFFLINE,
                    token_usage=0,
                    token_limit=config["token_limit"],
                    context7_queries=0,
                    context7_success_rate=0.0,
                    operations_completed=0,
                    avg_response_time=0.0,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    last_heartbeat=datetime.now() - timedelta(minutes=10)
                )
        
        self.agent_metrics = collected_metrics
        return collected_metrics
    
    async def get_agent_health(self, agent_name: str, config: Dict[str, Any]) -> AgentMetrics:
        """Get health metrics for a specific agent"""
        
        try:
            # Get Docker container info
            container = self.docker_client.containers.get(agent_name)
            container_stats = container.stats(stream=False)
            
            # Calculate resource usage
            cpu_usage = self.calculate_cpu_usage(container_stats)
            memory_usage = self.calculate_memory_usage(container_stats)
            
            # Simulate agent-specific metrics (in real implementation, these would come from agent APIs)
            if agent_name == "context7_agent":
                # Context7 agent is critical - higher usage expected
                token_usage = min(config["token_limit"] * 0.7, config["token_limit"])
                context7_queries = 50
                context7_success_rate = 98.5
                operations_completed = 45
            elif "agent" in agent_name:
                # Regular agents
                token_usage = min(config["token_limit"] * 0.6, config["token_limit"])
                context7_queries = 15 if config["cluster"] in ["implementation", "quality"] else 5
                context7_success_rate = 95.0 if config["cluster"] in ["implementation", "quality"] else 85.0
                operations_completed = 25
            else:
                token_usage = min(config["token_limit"] * 0.3, config["token_limit"])
                context7_queries = 5
                context7_success_rate = 90.0
                operations_completed = 10
            
            # Determine status based on metrics
            status = AgentStatus.HEALTHY
            if cpu_usage > 90 or memory_usage > 90:
                status = AgentStatus.CRITICAL
            elif cpu_usage > 70 or memory_usage > 70:
                status = AgentStatus.WARNING
            elif token_usage > config["token_limit"] * 0.9:
                status = AgentStatus.WARNING
            
            return AgentMetrics(
                agent_name=agent_name,
                cluster=config["cluster"],
                status=status,
                token_usage=int(token_usage),
                token_limit=config["token_limit"],
                context7_queries=context7_queries,
                context7_success_rate=context7_success_rate,
                operations_completed=operations_completed,
                avg_response_time=1.2,  # seconds
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                last_heartbeat=datetime.now()
            )
            
        except docker.errors.NotFound:
            # Container not found - agent is offline
            raise Exception(f"Container {agent_name} not found")
        except Exception as e:
            raise Exception(f"Error getting health for {agent_name}: {e}")
    
    def calculate_cpu_usage(self, stats: Dict[str, Any]) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_stats = stats['cpu_stats']
            precpu_stats = stats['precpu_stats']
            
            cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
            system_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
            
            cpu_count = cpu_stats.get('online_cpus', len(cpu_stats['cpu_usage'].get('percpu_usage', [1])))
            
            if system_delta > 0 and cpu_delta > 0:
                return (cpu_delta / system_delta) * cpu_count * 100
            return 0.0
        except (KeyError, ZeroDivisionError):
            return 0.0
    
    def calculate_memory_usage(self, stats: Dict[str, Any]) -> float:
        """Calculate memory usage percentage from Docker stats"""
        try:
            memory_stats = stats['memory_stats']
            usage = memory_stats['usage']
            limit = memory_stats['limit']
            
            return (usage / limit) * 100 if limit > 0 else 0.0
        except (KeyError, ZeroDivisionError):
            return 0.0
    
    async def calculate_platform_metrics(self) -> PlatformMetrics:
        """Calculate overall platform metrics"""
        
        if not self.agent_metrics:
            return self.platform_metrics
        
        # Basic counts
        total_agents = len(self.agent_metrics)
        healthy_agents = sum(1 for m in self.agent_metrics.values() 
                           if m.status == AgentStatus.HEALTHY)
        
        # Token usage
        total_token_usage = sum(m.token_usage for m in self.agent_metrics.values())
        
        # Context7 integration metrics
        agents_with_context7 = [m for m in self.agent_metrics.values() 
                              if m.cluster in ["implementation", "quality"] or m.agent_name == "context7_agent"]
        context7_integration_rate = (
            sum(m.context7_success_rate for m in agents_with_context7) / len(agents_with_context7)
            if agents_with_context7 else 0.0
        )
        
        # Performance metrics
        total_operations = sum(m.operations_completed for m in self.agent_metrics.values())
        operations_per_minute = total_operations  # Simplified - would be time-based in reality
        
        avg_context7_response_time = sum(m.avg_response_time for m in agents_with_context7) / len(agents_with_context7) if agents_with_context7 else 0.0
        
        # Cross-agent collaborations (simplified metric)
        cross_agent_collaborations = sum(m.operations_completed for m in self.agent_metrics.values() 
                                       if m.cluster == "coordination")
        
        # Platform efficiency score
        avg_health_score = sum(m.health_score for m in self.agent_metrics.values()) / total_agents if total_agents > 0 else 0.0
        token_efficiency = ((93000 - total_token_usage) / 93000) * 100 if total_token_usage < 93000 else 0.0
        platform_efficiency_score = (avg_health_score * 0.6) + (token_efficiency * 0.4)
        
        self.platform_metrics = PlatformMetrics(
            total_agents=total_agents,
            healthy_agents=healthy_agents,
            total_token_usage=total_token_usage,
            context7_integration_rate=context7_integration_rate,
            operations_per_minute=operations_per_minute,
            avg_context7_response_time=avg_context7_response_time,
            cross_agent_collaborations=cross_agent_collaborations,
            blocked_operations=0,  # Would track Context7 enforcer blocks
            platform_efficiency_score=platform_efficiency_score
        )
        
        return self.platform_metrics
    
    async def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on metrics"""
        
        recommendations = []
        
        # Token usage recommendations
        total_usage = sum(m.token_usage for m in self.agent_metrics.values())
        if total_usage > 70000:  # 75% of budget
            recommendations.append({
                "type": "token_optimization",
                "severity": "warning",
                "title": "High Token Usage Detected",
                "description": f"Platform using {total_usage}/93000 tokens ({(total_usage/93000)*100:.1f}%)",
                "recommendation": "Consider redistributing workload or optimizing agent queries"
            })
        
        # Context7 integration recommendations
        context7_agents = [m for m in self.agent_metrics.values() if m.context7_queries > 0]
        if context7_agents:
            avg_success_rate = sum(m.context7_success_rate for m in context7_agents) / len(context7_agents)
            if avg_success_rate < 95.0:
                recommendations.append({
                    "type": "context7_optimization", 
                    "severity": "warning",
                    "title": "Context7 Integration Issues",
                    "description": f"Context7 success rate: {avg_success_rate:.1f}%",
                    "recommendation": "Check Context7 server connectivity and query optimization"
                })
        
        # Agent health recommendations
        critical_agents = [m for m in self.agent_metrics.values() if m.status == AgentStatus.CRITICAL]
        if critical_agents:
            recommendations.append({
                "type": "agent_health",
                "severity": "critical", 
                "title": "Critical Agent Status",
                "description": f"{len(critical_agents)} agents in critical state",
                "recommendation": "Investigate and resolve critical agent issues immediately"
            })
        
        # Resource optimization
        high_cpu_agents = [m for m in self.agent_metrics.values() if m.cpu_usage > 80]
        if high_cpu_agents:
            recommendations.append({
                "type": "resource_optimization",
                "severity": "info",
                "title": "High CPU Usage",
                "description": f"{len(high_cpu_agents)} agents with high CPU usage",
                "recommendation": "Consider resource reallocation or agent optimization"
            })
        
        return recommendations
    
    def save_metrics_snapshot(self):
        """Save current metrics to history"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "platform_metrics": asdict(self.platform_metrics),
            "agent_metrics": {name: asdict(metrics) for name, metrics in self.agent_metrics.items()}
        }
        self.metrics_history.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]

# Flask Web Interface
app = Flask(__name__)
app.config['SECRET_KEY'] = 'platform-evolution-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

monitor = PlatformMonitor()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    return jsonify({
        "platform_metrics": asdict(monitor.platform_metrics),
        "agent_metrics": {name: asdict(metrics) for name, metrics in monitor.agent_metrics.items()}
    })

@app.route('/api/recommendations')
async def get_recommendations():
    recommendations = await monitor.generate_optimization_recommendations()
    return jsonify(recommendations)

@app.route('/api/history')
def get_history():
    return jsonify(monitor.metrics_history[-20:])  # Last 20 snapshots

@socketio.on('connect')
def handle_connect():
    emit('status', {'msg': 'Connected to Platform Evolution Monitor'})

async def monitoring_loop():
    """Main monitoring loop"""
    while True:
        try:
            logger.info("Collecting agent metrics...")
            await monitor.collect_agent_metrics()
            
            logger.info("Calculating platform metrics...")
            await monitor.calculate_platform_metrics()
            
            monitor.save_metrics_snapshot()
            
            # Emit real-time updates
            socketio.emit('metrics_update', {
                "platform_metrics": asdict(monitor.platform_metrics),
                "agent_metrics": {name: asdict(metrics) for name, metrics in monitor.agent_metrics.items()}
            })
            
            logger.info(f"Metrics updated - Platform efficiency: {monitor.platform_metrics.platform_efficiency_score:.1f}%")
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        await asyncio.sleep(30)  # Update every 30 seconds

if __name__ == '__main__':
    logger.info("Starting Platform Evolution Monitor...")
    
    # Start monitoring loop in background
    asyncio.create_task(monitoring_loop())
    
    # Start web interface
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)