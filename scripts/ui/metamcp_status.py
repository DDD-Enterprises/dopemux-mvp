#!/usr/bin/env python3
"""
MetaMCP Tmux Status Bar Script

Provides real-time visual feedback for ADHD-optimized development workflows.
Displays role, token usage, session info, and health status in tmux status bar.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple


class MetaMCPStatusBar:
    """ADHD-friendly tmux status bar for MetaMCP system."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.last_status_cache = None
        self.cache_timestamp = None
        self.cache_duration = 5  # seconds

        # ADHD-friendly color scheme
        self.colors = {
            'developer': '#4A90E2',      # Blue - calm focus
            'researcher': '#7ED321',     # Green - growth/learning
            'planner': '#F5A623',        # Orange - energy/planning
            'reviewer': '#D0021B',       # Red - attention/critical
            'ops': '#9013FE',            # Purple - operational
            'architect': '#50E3C2',      # Teal - strategic thinking
            'debugger': '#BD10E0',       # Magenta - problem solving
            'good': '#7ED321',           # Green for positive states
            'warning': '#F5A623',        # Orange for warnings
            'error': '#D0021B',          # Red for errors
            'neutral': '#9B9B9B'         # Gray for neutral
        }

        # Token usage thresholds for ADHD awareness
        self.token_thresholds = {
            'green': 0.6,    # < 60% usage
            'yellow': 0.8,   # 60-80% usage
            'orange': 0.9,   # 80-90% usage
            'red': 1.0       # > 90% usage
        }

    def get_metamcp_status(self) -> Optional[Dict]:
        """Get current MetaMCP status with caching."""
        now = datetime.now()

        # Use cache if available and fresh
        if (self.last_status_cache and self.cache_timestamp and
            (now - self.cache_timestamp).seconds < self.cache_duration):
            return self.last_status_cache

        try:
            # Try to get status from MetaMCP server
            result = subprocess.run([
                'python', str(self.project_root / 'metamcp_simple_query.py'),
                'get_status'
            ], capture_output=True, text=True, timeout=3)

            if result.returncode == 0:
                status = json.loads(result.stdout.strip())
                self.last_status_cache = status
                self.cache_timestamp = now
                return status

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass

        # Fallback: parse from recent logs or return minimal status
        return self._get_fallback_status()

    def _get_fallback_status(self) -> Dict:
        """Fallback status when MetaMCP is not directly accessible."""
        return {
            'role': 'unknown',
            'tools_count': 0,
            'token_usage': 0,
            'token_budget': 10000,
            'session_duration': 0,
            'health': 'unknown',
            'adhd_features': True
        }

    def format_role_indicator(self, role: str) -> str:
        """Format role with ADHD-friendly visual indicators."""
        role_icons = {
            'developer': '🧑‍💻',
            'researcher': '🔬',
            'planner': '📋',
            'reviewer': '👀',
            'ops': '⚙️',
            'architect': '🏗️',
            'debugger': '🐛',
            'unknown': '❓'
        }

        icon = role_icons.get(role, '❓')
        color = self.colors.get(role, self.colors['neutral'])

        return f"#[fg={color},bold]{icon} {role.upper()}#[default]"

    def format_token_usage(self, usage: int, budget: int) -> str:
        """Format token usage with ADHD-friendly progress visualization."""
        if budget == 0:
            percentage = 0
        else:
            percentage = usage / budget

        # Choose color based on usage
        if percentage < self.token_thresholds['green']:
            color = self.colors['good']
            icon = '💚'
        elif percentage < self.token_thresholds['yellow']:
            color = self.colors['warning']
            icon = '💛'
        elif percentage < self.token_thresholds['orange']:
            color = '#FF9500'  # Orange
            icon = '🧡'
        else:
            color = self.colors['error']
            icon = '❤️'

        # Create visual progress bar (5 segments)
        filled = int(percentage * 5)
        bar = '█' * filled + '░' * (5 - filled)

        return f"#[fg={color}]{icon} {usage/1000:.1f}k/{budget/1000:.0f}k #[fg=white]{bar}#[default]"

    def format_session_duration(self, duration_minutes: int) -> str:
        """Format session duration with ADHD break reminders."""
        if duration_minutes < 25:
            # Fresh session - green
            color = self.colors['good']
            icon = '🟢'
        elif duration_minutes < 50:
            # Time for break soon - yellow
            color = self.colors['warning']
            icon = '🟡'
        else:
            # Definitely time for break - gentle red
            color = self.colors['error']
            icon = '🔴'

        hours = duration_minutes // 60
        mins = duration_minutes % 60

        if hours > 0:
            time_str = f"{hours}h{mins:02d}m"
        else:
            time_str = f"{mins}m"

        return f"#[fg={color}]{icon} {time_str}#[default]"

    def format_health_status(self, health: str, tools_count: int) -> str:
        """Format health status with server connectivity."""
        if health == 'healthy' or health == 'good':
            color = self.colors['good']
            icon = '✅'
        elif health == 'warning':
            color = self.colors['warning']
            icon = '⚠️'
        elif health == 'error' or health == 'unhealthy':
            color = self.colors['error']
            icon = '❌'
        else:
            color = self.colors['neutral']
            icon = '❓'

        return f"#[fg={color}]{icon} {tools_count} tools#[default]"

    def format_adhd_indicators(self, adhd_features: bool) -> str:
        """Format ADHD accommodation status."""
        if adhd_features:
            return "#[fg=#7ED321]🧠 ADHD✓#[default]"
        else:
            return "#[fg=#9B9B9B]🧠 OFF#[default]"

    def get_current_time(self) -> str:
        """Get current time for reference."""
        return f"#[fg=#9B9B9B]{datetime.now().strftime('%H:%M')}#[default]"

    def generate_status_bar(self) -> str:
        """Generate complete tmux status bar string."""
        status = self.get_metamcp_status()

        if not status:
            return "#[fg=#D0021B]MetaMCP: Offline#[default]"

        # Extract status information
        role = status.get('role', 'unknown')
        tools_count = status.get('tools_count', 0)
        token_usage = status.get('token_usage', 0)
        token_budget = status.get('token_budget', 10000)
        session_duration = status.get('session_duration', 0)
        health = status.get('health', 'unknown')
        adhd_features = status.get('adhd_features', True)

        # Build status bar components
        components = [
            self.format_role_indicator(role),
            self.format_token_usage(token_usage, token_budget),
            self.format_session_duration(session_duration),
            self.format_health_status(health, tools_count),
            self.format_adhd_indicators(adhd_features),
            self.get_current_time()
        ]

        # Join with separators
        separator = " #[fg=#9B9B9B]|#[default] "
        return separator.join(components)

    def run_continuous(self, interval: int = 5):
        """Run status bar updates continuously."""
        while True:
            try:
                status_bar = self.generate_status_bar()
                print(status_bar, flush=True)
                time.sleep(interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"#[fg=#D0021B]Error: {str(e)}#[default]", flush=True)
                time.sleep(interval)


def main():
    """Main entry point for tmux status bar."""
    status_bar = MetaMCPStatusBar()

    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        # Run continuously for testing
        status_bar.run_continuous()
    else:
        # Single output for tmux
        print(status_bar.generate_status_bar())


if __name__ == '__main__':
    main()