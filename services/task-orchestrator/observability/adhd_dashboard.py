"""
ADHD Intelligence Dashboard Configuration

Grafana dashboard configuration for Component 6 observability.

Created: 2025-10-20
Component: 6 - Phase 1a (Observability Foundation)
Purpose: Visual dashboards for ADHD workflow metrics

Dashboard Panels:
1. Workflow Completion Rate (target: 85%)
2. Focus & Flow State Timeline
3. Cognitive Load Heatmap
4. Task Velocity Trends
5. Context Switch Frequency
"""

from typing import Dict, List, Any
import json


class ADHDDashboard:
    """
    Generates Grafana dashboard JSON for ADHD Intelligence metrics.

    Usage:
        dashboard = ADHDDashboard()
        config = dashboard.generate_dashboard()

        # Export to Grafana
        with open('adhd_dashboard.json', 'w') as f:
            json.dump(config, f, indent=2)
    """

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """
        Initialize dashboard generator.

        Args:
            prometheus_url: Prometheus datasource URL
        """
        self.prometheus_url = prometheus_url

    def generate_dashboard(self) -> Dict[str, Any]:
        """
        Generate complete Grafana dashboard configuration.

        Returns:
            Dict with Grafana JSON dashboard spec
        """
        return {
            "dashboard": {
                "title": "ADHD Intelligence Layer - Component 6",
                "tags": ["adhd", "component-6", "productivity"],
                "timezone": "browser",
                "refresh": "30s",
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "panels": self._generate_panels()
            }
        }

    def _generate_panels(self) -> List[Dict[str, Any]]:
        """Generate all dashboard panels."""
        return [
            self._panel_workflow_completion_rate(),
            self._panel_focus_duration_histogram(),
            self._panel_flow_state_timeline(),
            self._panel_cognitive_load_gauge(),
            self._panel_cognitive_load_heatmap(),
            self._panel_task_velocity(),
            self._panel_context_switches(),
            self._panel_recovery_time(),
        ]

    def _panel_workflow_completion_rate(self) -> Dict[str, Any]:
        """
        Panel 1: Task completion rate (target: 85%).

        Shows: completed / started ratio
        """
        return {
            "id": 1,
            "title": "🎯 Workflow Completion Rate (Target: 85%)",
            "type": "gauge",
            "gridPos": {"x": 0, "y": 0, "w": 6, "h": 8},
            "targets": [{
                "expr": """
                    (
                        sum(rate(adhd_tasks_completed_total[1h]))
                        /
                        sum(rate(adhd_tasks_started_total[1h]))
                    ) * 100
                """,
                "legendFormat": "Completion Rate %"
            }],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "red"},
                            {"value": 70, "color": "yellow"},
                            {"value": 85, "color": "green"}
                        ]
                    },
                    "unit": "percent",
                    "min": 0,
                    "max": 100
                }
            }
        }

    def _panel_focus_duration_histogram(self) -> Dict[str, Any]:
        """
        Panel 2: Focus session duration distribution.

        Shows: Histogram of focus session lengths
        """
        return {
            "id": 2,
            "title": "⏱️  Focus Session Duration Distribution",
            "type": "histogram",
            "gridPos": {"x": 6, "y": 0, "w": 9, "h": 8},
            "targets": [{
                "expr": "adhd_focus_duration_seconds",
                "legendFormat": "Focus Duration"
            }],
            "description": "Distribution of focus session lengths. ADHD optimal: 15-45 minutes."
        }

    def _panel_flow_state_timeline(self) -> Dict[str, Any]:
        """
        Panel 3: Flow state timeline.

        Shows: When user is in flow state (1) vs not (0)
        """
        return {
            "id": 3,
            "title": "🌊 Flow State Timeline",
            "type": "timeseries",
            "gridPos": {"x": 15, "y": 0, "w": 9, "h": 8},
            "targets": [{
                "expr": "adhd_current_flow_state",
                "legendFormat": "In Flow"
            }],
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "fillOpacity": 50,
                        "lineWidth": 2
                    },
                    "color": {
                        "mode": "thresholds"
                    },
                    "thresholds": {
                        "steps": [
                            {"value": 0, "color": "gray"},
                            {"value": 1, "color": "green"}
                        ]
                    }
                }
            },
            "description": "Green areas indicate hyperfocus/flow state (protect from interruptions)"
        }

    def _panel_cognitive_load_gauge(self) -> Dict[str, Any]:
        """
        Panel 4: Current cognitive load gauge.

        Shows: Real-time cognitive load score (0.0-1.0)
        """
        return {
            "id": 4,
            "title": "🧠 Current Cognitive Load",
            "type": "gauge",
            "gridPos": {"x": 0, "y": 8, "w": 6, "h": 8},
            "targets": [{
                "expr": 'adhd_cognitive_load{load_category="optimal"}',
                "legendFormat": "Load Score"
            }],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"value": 0, "color": "blue"},      # Low (boredom risk)
                            {"value": 0.3, "color": "green"},    # Entering optimal
                            {"value": 0.6, "color": "green"},    # Optimal sweet spot
                            {"value": 0.7, "color": "yellow"},   # Leaving optimal
                            {"value": 0.85, "color": "red"}      # Overwhelm
                        ]
                    },
                    "unit": "percentunit",
                    "min": 0,
                    "max": 1
                }
            },
            "description": "Green (0.6-0.7) = optimal. Red (>0.85) = take break immediately!"
        }

    def _panel_cognitive_load_heatmap(self) -> Dict[str, Any]:
        """
        Panel 5: Cognitive load heatmap by hour of day.

        Shows: When cognitive load is highest/lowest
        """
        return {
            "id": 5,
            "title": "📊 Cognitive Load Heatmap (by Hour)",
            "type": "heatmap",
            "gridPos": {"x": 6, "y": 8, "w": 9, "h": 8},
            "targets": [{
                "expr": """
                    avg_over_time(
                        adhd_cognitive_load_distribution[1h]
                    )
                """,
                "legendFormat": "Load by Hour"
            }],
            "description": "Learn your daily cognitive load patterns - when are you most/least productive?"
        }

    def _panel_task_velocity(self) -> Dict[str, Any]:
        """
        Panel 6: Task completion velocity.

        Shows: Tasks completed per day (rolling average)
        """
        return {
            "id": 6,
            "title": "🚀 Task Velocity (Tasks/Day)",
            "type": "timeseries",
            "gridPos": {"x": 15, "y": 8, "w": 9, "h": 8},
            "targets": [
                {
                    "expr": "adhd_task_velocity_per_day",
                    "legendFormat": "Raw Velocity"
                },
                {
                    "expr": "adhd_complexity_adjusted_velocity",
                    "legendFormat": "Complexity-Adjusted"
                }
            ],
            "description": "Track productivity trends. Complexity-adjusted velocity accounts for hard tasks."
        }

    def _panel_context_switches(self) -> Dict[str, Any]:
        """
        Panel 7: Context switch frequency.

        Shows: Context switches per day by reason
        """
        return {
            "id": 7,
            "title": "🔄 Context Switches per Day",
            "type": "timeseries",
            "gridPos": {"x": 0, "y": 16, "w": 12, "h": 8},
            "targets": [{
                "expr": """
                    sum by (switch_reason) (
                        rate(adhd_context_switches_total[1h]) * 86400
                    )
                """,
                "legendFormat": "{{switch_reason}}"
            }],
            "description": "Green: intentional switches. Yellow: break returns. Red: interrupts."
        }

    def _panel_recovery_time(self) -> Dict[str, Any]:
        """
        Panel 8: Context switch recovery time distribution.

        Shows: How long it takes to recover from switches
        """
        return {
            "id": 8,
            "title": "⏱️  Context Switch Recovery Time",
            "type": "histogram",
            "gridPos": {"x": 12, "y": 16, "w": 12, "h": 8},
            "targets": [{
                "expr": "adhd_context_switch_recovery_seconds",
                "legendFormat": "Recovery Time"
            }],
            "description": "Target: < 2 seconds (with Context Switch Recovery Engine). Neurotypical: 5-10 min. ADHD without tool: 15-25 min."
        }

    def export_to_file(self, filename: str = "adhd_dashboard.json"):
        """
        Export dashboard configuration to JSON file.

        Args:
            filename: Output filename
        """
        config = self.generate_dashboard()
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ Dashboard exported to {filename}")
        print(f"Import to Grafana: Dashboards → Import → Upload JSON file")


def generate_default_dashboard() -> str:
    """
    Generate default ADHD Intelligence dashboard.

    Returns:
        Path to exported dashboard JSON
    """
    dashboard = ADHDDashboard()
    output_path = "/tmp/adhd_intelligence_dashboard.json"
    dashboard.export_to_file(output_path)
    return output_path


if __name__ == "__main__":
    # Generate dashboard when run directly
    path = generate_default_dashboard()
    print(f"\n📊 Dashboard ready: {path}")
    print("\nNext steps:")
    print("1. Start Prometheus (if not running)")
    print("2. Start Grafana (if not running)")
    print("3. Import dashboard JSON to Grafana")
    print("4. Configure Prometheus datasource in Grafana")
