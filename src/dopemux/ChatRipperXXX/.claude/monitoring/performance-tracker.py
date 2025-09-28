#!/usr/bin/env python3
"""
MCP Performance Monitoring System
Tracks usage patterns, optimizes context, and provides performance insights
"""

import json
import time
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import yaml

class MCPPerformanceTracker:
    def __init__(self):
        self.monitoring_dir = Path('.claude/monitoring')
        self.monitoring_dir.mkdir(exist_ok=True)

        # Configuration
        self.config_file = self.monitoring_dir / 'config.yaml'
        self.metrics_file = self.monitoring_dir / 'metrics.json'
        self.performance_log = self.monitoring_dir / 'performance.log'

        # Load configuration
        self.config = self._load_config()

        # Session tracking
        self.current_session = {
            'start_time': datetime.now(),
            'metrics': {},
            'server_calls': [],
            'context_snapshots': []
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Default monitoring configuration"""
        return {
            'metrics': {
                'context_usage': {
                    'warn_threshold': 0.7,
                    'critical_threshold': 0.85,
                    'check_interval': 60
                }
            },
            'memory_cache': {
                'max_size_mb': 512,
                'ttl_seconds': 3600
            }
        }

    def track_server_call(self, server_name: str, method: str, tokens_used: int,
                          latency_ms: float, success: bool, error: str = ""):
        """Track MCP server call performance"""
        call_record = {
            'timestamp': datetime.now().isoformat(),
            'server': server_name,
            'method': method,
            'tokens_used': tokens_used,
            'latency_ms': latency_ms,
            'success': success,
            'error': error
        }

        self.current_session['server_calls'].append(call_record)

        # Update metrics
        if server_name not in self.current_session['metrics']:
            self.current_session['metrics'][server_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_tokens': 0,
                'total_latency': 0,
                'average_latency': 0
            }

        metrics = self.current_session['metrics'][server_name]
        metrics['total_calls'] += 1
        if success:
            metrics['successful_calls'] += 1
        else:
            metrics['failed_calls'] += 1

        metrics['total_tokens'] += tokens_used
        metrics['total_latency'] += latency_ms
        metrics['average_latency'] = metrics['total_latency'] / metrics['total_calls']

        # Check thresholds
        self._check_thresholds(call_record)

    def _check_thresholds(self, call_record: Dict[str, Any]):
        """Check performance thresholds and trigger actions"""
        config = self.config.get('metrics', {})

        # Latency check
        if 'latency_ms' in call_record:
            latency_config = config.get('server_latency', {})
            max_acceptable = latency_config.get('max_acceptable_ms', 500)

            if call_record['latency_ms'] > max_acceptable:
                self._log_alert('LATENCY_EXCEEDED',
                               f"Server {call_record['server']} latency: {call_record['latency_ms']}ms > {max_acceptable}ms")

        # Token spike check
        if 'tokens_used' in call_record:
            token_config = config.get('token_consumption', {})
            spike_threshold = token_config.get('spike_threshold', 5000)

            if call_record['tokens_used'] > spike_threshold:
                self._log_alert('TOKEN_SPIKE',
                               f"Server {call_record['server']} token usage: {call_record['tokens_used']} > {spike_threshold}")

    def _log_alert(self, alert_type: str, message: str):
        """Log performance alerts"""
        alert_record = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'session_duration': str(datetime.now() - self.current_session['start_time'])
        }

        # Write to alerts file
        alerts_file = self.monitoring_dir / 'alerts.json'
        try:
            if alerts_file.exists():
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
            else:
                alerts = {'alerts': []}

            alerts['alerts'].append(alert_record)

            with open(alerts_file, 'w') as f:
                json.dump(alerts, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not write alert: {e}")

        # Also write to performance log
        self._write_performance_log(f"ALERT {alert_type}: {message}")

    def snapshot_context_usage(self, usage_percent: float, total_tokens: int):
        """Record context usage snapshot"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'usage_percent': usage_percent,
            'total_tokens': total_tokens,
            'session_duration': str(datetime.now() - self.current_session['start_time'])
        }

        self.current_session['context_snapshots'].append(snapshot)

        # Check context thresholds
        context_config = self.config.get('metrics', {}).get('context_usage', {})
        warn_threshold = context_config.get('warn_threshold', 0.7)
        critical_threshold = context_config.get('critical_threshold', 0.85)

        if usage_percent > critical_threshold:
            self._log_alert('CONTEXT_CRITICAL',
                           ".2f")
            # Trigger context compaction
            self._trigger_context_compaction()
        elif usage_percent > warn_threshold:
            self._log_alert('CONTEXT_WARNING',
                           ".2f")

    def _trigger_context_compaction(self):
        """Trigger automatic context compaction"""
        self._write_performance_log("TRIGGERING_CONTEXT_COMPACTION")

        # This would integrate with Claude Code's context management
        # For now, just log the trigger
        compaction_record = {
            'timestamp': datetime.now().isoformat(),
            'action': 'context_compaction_triggered',
            'reason': 'usage_above_critical_threshold'
        }

        compaction_file = self.monitoring_dir / 'compactions.json'
        try:
            if compaction_file.exists():
                with open(compaction_file, 'r') as f:
                    compactions = json.load(f)
            else:
                compactions = {'compactions': []}

            compactions['compactions'].append(compaction_record)

            with open(compaction_file, 'w') as f:
                json.dump(compactions, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not record compaction: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'session_info': {
                'start_time': self.current_session['start_time'].isoformat(),
                'duration': str(datetime.now() - self.current_session['start_time']),
                'total_server_calls': len(self.current_session['server_calls'])
            },
            'server_metrics': {},
            'context_analysis': {},
            'recommendations': []
        }

        # Server metrics analysis
        for server, metrics in self.current_session['metrics'].items():
            report['server_metrics'][server] = metrics

            # Generate recommendations
            if metrics['total_calls'] > 0:
                success_rate = metrics['successful_calls'] / metrics['total_calls']
                if success_rate < 0.95:
                    report['recommendations'].append(
                        f"Investigate {server} failures: {metrics['failed_calls']} failed calls")

                if metrics['average_latency'] > 500:
                    report['recommendations'].append(
                        ".1f")

        # Context analysis
        if self.current_session['context_snapshots']:
            snapshots = self.current_session['context_snapshots']
            avg_usage = sum(s['usage_percent'] for s in snapshots) / len(snapshots)
            max_usage = max(s['usage_percent'] for s in snapshots)

            report['context_analysis'] = {
                'average_usage': avg_usage,
                'max_usage': max_usage,
                'snapshot_count': len(snapshots)
            }

            if max_usage > 0.8:
                report['recommendations'].append("High context usage detected - consider compaction")

        return report

    def _write_performance_log(self, message: str):
        """Write to performance log"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.performance_log, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Warning: Could not write to performance log: {e}")

    def save_session_metrics(self):
        """Save current session metrics to file"""
        try:
            session_data = {
                'session': self.current_session,
                'performance_report': self.get_performance_report(),
                'timestamp': datetime.now().isoformat()
            }

            # Append to metrics file
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {'sessions': []}

            existing_data['sessions'].append(session_data)

            # Keep only last 10 sessions
            if len(existing_data['sessions']) > 10:
                existing_data['sessions'] = existing_data['sessions'][-10:]

            with open(self.metrics_file, 'w') as f:
                json.dump(existing_data, f, indent=2, default=str)

        except Exception as e:
            print(f"Warning: Could not save session metrics: {e}")

def main():
    """Main monitoring function for integration"""
    tracker = MCPPerformanceTracker()

    # Example usage (would be called from MCP hooks)
    # tracker.track_server_call('OpenMemory', 'search', 150, 45.2, True)
    # tracker.snapshot_context_usage(0.65, 12500)
    # tracker.save_session_metrics()

    print("MCP Performance Tracker initialized")
    print(f"Monitoring directory: {tracker.monitoring_dir}")
    print(f"Configuration loaded: {tracker.config_file.exists()}")

    # Generate sample report
    report = tracker.get_performance_report()
    print(f"Current session duration: {report['session_info']['duration']}")
    print(f"Total server calls: {report['session_info']['total_server_calls']}")

    if report['recommendations']:
        print("Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == '__main__':
    main()