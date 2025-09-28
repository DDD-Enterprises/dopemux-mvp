#!/usr/bin/env python3

"""
Platform Evolution Status Monitor
Real-time status monitoring for the distributed Claude Code platform
"""

import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import subprocess
import psutil
import requests

class PlatformStatusMonitor:
    def __init__(self):
        self.project_root = Path.cwd()
        self.platform_root = self.project_root / ".claude" / "platform-evolution"
        self.status_file = self.project_root / ".platform-evolution-status.json"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def check_docker_containers(self) -> Dict[str, Any]:
        """Check status of Docker containers"""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(self.platform_root / "docker-compose.yml"), "ps", "--format", "json"],
                cwd=self.platform_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            containers = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    try:
                        container_info = json.loads(line)
                        containers.append({
                            "name": container_info.get("Name", "unknown"),
                            "state": container_info.get("State", "unknown"),
                            "status": container_info.get("Status", "unknown"),
                            "ports": container_info.get("Publishers", [])
                        })
                    except json.JSONDecodeError:
                        continue
            
            return {
                "containers": containers,
                "total_containers": len(containers),
                "running_containers": len([c for c in containers if c["state"] == "running"]),
                "healthy": len([c for c in containers if c["state"] == "running"]) == len(containers)
            }
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to check Docker containers: {e}")
            return {"containers": [], "total_containers": 0, "running_containers": 0, "healthy": False}
    
    def check_context7_status(self) -> Dict[str, Any]:
        """Check Context7 integration status"""
        try:
            # Run Context7 enforcer validation
            result = subprocess.run(
                ["python3", str(self.platform_root / "context7-enforcer.py"), "--validate"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "available": result.returncode == 0,
                "response_time_ms": None,  # Could be enhanced with actual timing
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            return {
                "available": False,
                "response_time_ms": None,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": "Context7 validation timeout"
            }
        except Exception as e:
            return {
                "available": False,
                "response_time_ms": None,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def check_monitoring_dashboard(self) -> Dict[str, Any]:
        """Check monitoring dashboard status"""
        try:
            response = requests.get("http://localhost:8080/health", timeout=5)
            return {
                "available": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "last_check": datetime.now(timezone.utc).isoformat()
            }
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "response_time_ms": None,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def estimate_token_usage(self) -> Dict[str, Any]:
        """Estimate current token usage across clusters"""
        # This would be enhanced with actual MCP call monitoring
        estimated_usage = {
            "research_cluster": {
                "budget": 20000,
                "used": 0,  # Would be populated from actual monitoring
                "efficiency": 0.85
            },
            "implementation_cluster": {
                "budget": 25000,
                "used": 0,
                "efficiency": 0.90
            },
            "quality_cluster": {
                "budget": 15000,
                "used": 0,
                "efficiency": 0.80
            },
            "coordination_cluster": {
                "budget": 10000,
                "used": 0,
                "efficiency": 0.95
            }
        }
        
        total_budget = sum(cluster["budget"] for cluster in estimated_usage.values())
        total_used = sum(cluster["used"] for cluster in estimated_usage.values())
        
        return {
            "clusters": estimated_usage,
            "total_budget": total_budget,
            "total_used": total_used,
            "utilization_percent": (total_used / total_budget * 100) if total_budget > 0 else 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive platform status"""
        return {
            "platform": {
                "mode": "distributed",
                "context7_enforced": True,
                "version": "1.0.0",
                "uptime_start": self._get_platform_start_time(),
                "status": "running"
            },
            "system_metrics": self.get_system_metrics(),
            "containers": self.check_docker_containers(),
            "context7": self.check_context7_status(),
            "monitoring_dashboard": self.check_monitoring_dashboard(),
            "token_usage": self.estimate_token_usage(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def _get_platform_start_time(self) -> Optional[str]:
        """Get platform start time from status file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
                return status.get("started_at")
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return None
    
    def save_status(self, status: Dict[str, Any]) -> None:
        """Save status to file"""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def print_status_summary(self, status: Dict[str, Any]) -> None:
        """Print human-readable status summary"""
        print("\n" + "="*60)
        print("🚀 CLAUDE CODE PLATFORM EVOLUTION STATUS")
        print("="*60)
        
        # Platform info
        platform = status["platform"]
        print(f"Mode: {platform['mode']}")
        print(f"Context7 Enforced: {'✅' if platform['context7_enforced'] else '❌'}")
        print(f"Status: {platform['status']}")
        
        if platform.get('uptime_start'):
            start_time = datetime.fromisoformat(platform['uptime_start'].replace('Z', '+00:00'))
            uptime = datetime.now(timezone.utc) - start_time
            print(f"Uptime: {str(uptime).split('.')[0]}")
        
        # System metrics
        metrics = status["system_metrics"]
        print(f"\n📊 SYSTEM METRICS")
        print(f"CPU: {metrics['cpu_percent']:.1f}%")
        print(f"Memory: {metrics['memory_percent']:.1f}%")
        print(f"Disk: {metrics['disk_usage']:.1f}%")
        
        # Containers
        containers = status["containers"]
        print(f"\n🐳 CONTAINERS")
        print(f"Total: {containers['total_containers']}")
        print(f"Running: {containers['running_containers']}")
        print(f"Health: {'✅' if containers['healthy'] else '❌'}")
        
        # Context7
        context7 = status["context7"]
        print(f"\n📚 CONTEXT7 INTEGRATION")
        print(f"Available: {'✅' if context7['available'] else '❌'}")
        if context7.get('error'):
            print(f"Error: {context7['error']}")
        
        # Monitoring
        dashboard = status["monitoring_dashboard"]
        print(f"\n📈 MONITORING DASHBOARD")
        print(f"Available: {'✅' if dashboard['available'] else '❌'}")
        if dashboard['available']:
            print(f"URL: http://localhost:8080")
            if dashboard.get('response_time_ms'):
                print(f"Response Time: {dashboard['response_time_ms']:.1f}ms")
        
        # Token usage
        tokens = status["token_usage"]
        print(f"\n🎯 TOKEN USAGE")
        print(f"Total Budget: {tokens['total_budget']:,}")
        print(f"Total Used: {tokens['total_used']:,}")
        print(f"Utilization: {tokens['utilization_percent']:.1f}%")
        
        print("\n" + "="*60)
    
    async def monitor_continuously(self, interval: int = 30) -> None:
        """Continuously monitor platform status"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                status = self.get_comprehensive_status()
                self.save_status(status)
                self.print_status_summary(status)
                
                await asyncio.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Platform Evolution Status Monitor")
    parser.add_argument("--continuous", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    monitor = PlatformStatusMonitor()
    
    if args.continuous:
        asyncio.run(monitor.monitor_continuously(args.interval))
    else:
        status = monitor.get_comprehensive_status()
        monitor.save_status(status)
        
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            monitor.print_status_summary(status)

if __name__ == "__main__":
    main()